import asyncio
import io
import logging

import aiosqlite
import discord
import requests
from discord.ext import commands

from cogs.utils.constants import (BOTVERSION, COMMAND_PREFIX,
                                  IMAGE_SCREEN_FLAGGED_KEYWORDS,
                                  IMAGE_SCREEN_MODEL, MSG_DEL_DELAY, OWNER_ID,
                                  PERMISSIONS_DATABASE)

logger = logging.getLogger(__name__)

# Global model reference — loaded once on first use to avoid slow startup
_pipeline = None
_model_loading = False

def get_pipeline():
    """
    Lazy-load the HuggingFace image-to-text pipeline.
    The model is downloaded on first run and cached by transformers.
    """
    global _pipeline, _model_loading
    if _pipeline is None and not _model_loading:
        _model_loading = True
        try:
            from transformers import pipeline as hf_pipeline
            logger.info(f"Loading image-to-text model: {IMAGE_SCREEN_MODEL}")
            _pipeline = hf_pipeline("image-to-text", model=IMAGE_SCREEN_MODEL)
            logger.info("Image-to-text model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load image-to-text model: {e}")
            _pipeline = None
        finally:
            _model_loading = False
    return _pipeline


class ImageScreen(commands.Cog):
    '''
    Image screening module using a local HuggingFace image-to-text model.
    Automatically describes images posted in enabled channels and flags
    potentially inappropriate content.
    '''
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Image screening module online')
        # Pre-load the model in a background thread so it's ready when needed
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, get_pipeline)

    # ─── Automatic image screening on message ───────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots and DMs
        if message.author.bot or message.guild is None:
            return

        # Only process messages that have image attachments
        image_attachments = [
            att for att in message.attachments
            if att.content_type and att.content_type.startswith('image/')
        ]
        if not image_attachments:
            return

        # Check if image screening is enabled for this channel
        guild_id = message.guild.id
        channel_id = message.channel.id

        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute(
                'SELECT enabled FROM imagescreen WHERE server_id = ? AND channel_id = ?',
                (guild_id, channel_id)
            ) as cursor:
                result = await cursor.fetchone()
                enabled = result is not None and result[0]

        if not enabled:
            return

        # Screen every image attachment
        for attachment in image_attachments:
            description = await self._describe_image_from_url(attachment.url)
            if description is None:
                continue

            flagged = self._check_flagged(description)
            if flagged:
                log_channel = discord.utils.get(message.guild.text_channels, name='image-screen-log')
                embed = discord.Embed(
                    title='⚠ Flagged Image Detected',
                    description=f'**Caption:** {description}\n'
                                f'**Flagged keywords:** {", ".join(flagged)}\n'
                                f'**Author:** {message.author.mention}\n'
                                f'**Channel:** {message.channel.mention}\n'
                                f'**[Jump to message]({message.jump_url})**',
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=attachment.url)
                embed.set_footer(text=BOTVERSION)

                if log_channel:
                    await log_channel.send(embed=embed)
                else:
                    # Fallback: notify in the same channel (ephemeral-style)
                    await message.channel.send(
                        embed=embed, delete_after=30
                    )

    # ─── Manual describe command ─────────────────────────────────────────

    @commands.command(name='describe', aliases=['caption', 'imgdesc'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def describe_image(self, ctx):
        '''
        Describe an image using the local AI model.
        Attach an image or reply to a message containing one.
        '''
        attachment = None

        # Check for attachment on the command message itself
        if ctx.message.attachments:
            for att in ctx.message.attachments:
                if att.content_type and att.content_type.startswith('image/'):
                    attachment = att
                    break

        # Check if replying to a message with an attachment
        if attachment is None and ctx.message.reference:
            resolved = ctx.message.reference.resolved
            if resolved and resolved.attachments:
                for att in resolved.attachments:
                    if att.content_type and att.content_type.startswith('image/'):
                        attachment = att
                        break

        if attachment is None:
            await ctx.reply(
                'Attach an image or reply to a message with an image to describe it.',
                mention_author=False, delete_after=MSG_DEL_DELAY
            )
            return

        async with ctx.typing():
            description = await self._describe_image_from_url(attachment.url)

        if description:
            embed = discord.Embed(
                title='Image Description',
                description=description,
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=attachment.url)
            embed.set_footer(text=f'Model: {IMAGE_SCREEN_MODEL}')
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await ctx.reply(
                'Could not describe that image. The model may still be loading — try again shortly.',
                mention_author=False, delete_after=MSG_DEL_DELAY
            )

    # ─── Model status command ────────────────────────────────────────────

    @commands.command(name='screeninfo')
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def screen_info(self, ctx):
        '''
        Show the current image screening model status and configuration.
        '''
        pipe = get_pipeline()
        status = '✅ Loaded' if pipe is not None else ('⏳ Loading...' if _model_loading else '❌ Not loaded')
        embed = discord.Embed(title='Image Screening Info', color=discord.Color.blurple())
        embed.add_field(name='Model', value=IMAGE_SCREEN_MODEL, inline=False)
        embed.add_field(name='Status', value=status, inline=False)
        embed.add_field(name='Flagged Keywords', value=', '.join(IMAGE_SCREEN_FLAGGED_KEYWORDS) or 'None', inline=False)
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    # ─── Internal helpers ────────────────────────────────────────────────

    async def _describe_image_from_url(self, url: str) -> str | None:
        """Download an image from a URL and run it through the model."""
        pipe = get_pipeline()
        if pipe is None:
            return None

        try:
            # Download on a thread so we don't block the event loop
            loop = asyncio.get_event_loop()
            image_bytes = await loop.run_in_executor(None, lambda: requests.get(url).content)

            from PIL import Image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

            # Run inference on a thread (model is CPU/GPU-bound)
            result = await loop.run_in_executor(None, lambda: pipe(image))

            if result and isinstance(result, list):
                return result[0].get('generated_text', '').strip()
        except Exception as e:
            logger.error(f"Error describing image: {e}")
        return None

    @staticmethod
    def _check_flagged(description: str) -> list[str]:
        """Check if the description contains any flagged keywords."""
        description_lower = description.lower()
        return [kw for kw in IMAGE_SCREEN_FLAGGED_KEYWORDS if kw.lower() in description_lower]


async def setup(bot):
    await bot.add_cog(ImageScreen(bot))
