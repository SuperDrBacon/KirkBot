import asyncio
import io
from datetime import timedelta

import aiosqlite
import discord
import requests
from discord.ext import commands

from cogs.utils.constants import (BOTVERSION, COMMAND_PREFIX,
                                  DEFAULT_IMAGEMOD_FLAGGED_KEYWORDS,
                                  IMAGEMOD_CLASSIFICATION_THRESHOLD,
                                  IMAGEMOD_DATABASE, MSG_DEL_DELAY, OWNER_ID,
                                  PERMISSIONS_DATABASE)

# ─── Image action buttons view ───────────────────────────────────────────

class ImageActionView(discord.ui.View):
    """View with buttons to mute the flagged user and/or delete the flagged message."""

    def __init__(self, member: discord.Member, flagged_message: discord.Message):
        super().__init__(timeout=300)  # buttons expire after 5 minutes
        self.member = member
        self.flagged_message = flagged_message

    async def _check_perms(self, interaction: discord.Interaction, perm: str) -> bool:
        """Check that the moderator has the required permission."""
        if not getattr(interaction.user.guild_permissions, perm, False):
            await interaction.response.send_message(
                f'You do not have the `{perm}` permission.', ephemeral=True
            )
            return False
        return True

    async def _disable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Disable a single button and update the message."""
        button.disabled = True
        await interaction.message.edit(view=self)

    async def do_mute(self, interaction: discord.Interaction, button: discord.ui.Button, minutes: int):
        """Apply a timeout to the member."""
        if not await self._check_perms(interaction, 'moderate_members'):
            return

        try:
            await self.member.timeout(
                timedelta(minutes=minutes),
                reason=f'Flagged image — muted for {minutes}min by {interaction.user}'
            )
            await interaction.response.send_message(
                f'🔇 **{self.member.display_name}** has been muted for **{minutes} minute{"s" if minutes != 1 else ""}**.',
                ephemeral=True
            )
            await self._disable_button(interaction, button)
        except discord.Forbidden:
            await interaction.response.send_message(
                'I don\'t have permission to mute that member. Check my role hierarchy.',
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f'Failed to mute: {e}', ephemeral=True)

    @discord.ui.button(label='Mute 1 min', style=discord.ButtonStyle.secondary, emoji='🔇')
    async def mute_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_mute(interaction, button, 1)

    @discord.ui.button(label='Mute 5 min', style=discord.ButtonStyle.primary, emoji='🔇')
    async def mute_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_mute(interaction, button, 5)

    @discord.ui.button(label='Mute 30 min', style=discord.ButtonStyle.danger, emoji='🔇')
    async def mute_30(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_mute(interaction, button, 30)

    @discord.ui.button(label='Delete Image', style=discord.ButtonStyle.danger, emoji='🗑️')
    async def delete_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_perms(interaction, 'manage_messages'):
            return

        try:
            await self.flagged_message.delete()
            await interaction.response.send_message(
                f'🗑️ Flagged message by **{self.member.display_name}** has been deleted.',
                ephemeral=True
            )
            await self._disable_button(interaction, button)
        except discord.NotFound:
            await interaction.response.send_message('Message was already deleted.', ephemeral=True)
            await self._disable_button(interaction, button)
        except discord.Forbidden:
            await interaction.response.send_message(
                'I don\'t have permission to delete that message.',
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f'Failed to delete: {e}', ephemeral=True)


# ─── Dynamic model manager ──────────────────────────────────────────────

class ModelManager:
    """
    Manages two HuggingFace models that can run simultaneously:
      - captioning      : image-to-text (e.g. BLIP) → generates a caption → keyword flagging
      - classification  : image-classification (e.g. Falconsai/nsfw_image_detection) → label + score
    Models are loaded globally; per-server enable/disable/threshold is handled by the cog.
    """
    def __init__(self):
        # Captioning model
        self.captioning_model_name: str | None = None
        self.captioning_processor = None
        self.captioning_model = None
        self.captioning_ready: bool = False
        self.captioning_loading: bool = False

        # Classification model
        self.classification_model_name: str | None = None
        self.classification_pipeline = None
        self.classification_ready: bool = False
        self.classification_loading: bool = False

    async def load_global_settings(self):
        """Read global model names from the imagemod database (SERVER_ID=0)."""
        settings: dict[str, str] = {}
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            async with con.execute(
                'SELECT KEY, VALUE FROM settings WHERE SERVER_ID = 0'
            ) as cur:
                async for row in cur:
                    settings[row[0]] = row[1]
        self.captioning_model_name = settings.get('captioning_model')
        self.classification_model_name = settings.get('classification_model')

    # ── Captioning loader ────────────────────────────────────────────

    def load_captioning_sync(self, name: str):
        from transformers import BlipForConditionalGeneration, BlipProcessor
        processor = BlipProcessor.from_pretrained(name)
        model = BlipForConditionalGeneration.from_pretrained(name)
        return processor, model

    async def ensure_captioning_loaded(self):
        if self.captioning_ready or self.captioning_loading:
            return
        if not self.captioning_model_name:
            return
        self.captioning_loading = True
        try:
            loop = asyncio.get_event_loop()
            processor, model = await loop.run_in_executor(
                None, self.load_captioning_sync, self.captioning_model_name
            )
            self.captioning_processor = processor
            self.captioning_model = model
            self.captioning_ready = True
            print(f'Captioning model loaded: {self.captioning_model_name}')
        except Exception as e:
            self.captioning_processor = None
            self.captioning_model = None
            self.captioning_ready = False
            print(f'Failed to load captioning model: {e}')
        finally:
            self.captioning_loading = False

    async def reload_captioning(self):
        self.captioning_ready = False
        self.captioning_processor = None
        self.captioning_model = None
        await self.ensure_captioning_loaded()

    # ── Classification loader ────────────────────────────────────────

    def load_classification_sync(self, name: str):
        from transformers import pipeline as hf_pipeline
        return hf_pipeline('image-classification', model=name)

    async def ensure_classification_loaded(self):
        if self.classification_ready or self.classification_loading:
            return
        if not self.classification_model_name:
            return
        self.classification_loading = True
        try:
            loop = asyncio.get_event_loop()
            pipe = await loop.run_in_executor(
                None, self.load_classification_sync, self.classification_model_name
            )
            self.classification_pipeline = pipe
            self.classification_ready = True
            print(f'Classification model loaded: {self.classification_model_name}')
        except Exception as e:
            self.classification_pipeline = None
            self.classification_ready = False
            print(f'Failed to load classification model: {e}')
        finally:
            self.classification_loading = False

    async def reload_classification(self):
        self.classification_ready = False
        self.classification_pipeline = None
        await self.ensure_classification_loaded()

    # ── Boot both ────────────────────────────────────────────────────

    async def ensure_all_loaded(self):
        await self.load_global_settings()
        tasks = []
        if not self.captioning_ready:
            tasks.append(self.ensure_captioning_loaded())
        if not self.classification_ready:
            tasks.append(self.ensure_classification_loaded())
        if tasks:
            await asyncio.gather(*tasks)


model_manager = ModelManager()


class Imagemod(commands.Cog):
    '''
    Image screening module using a local HuggingFace image-to-text model.
    Automatically describes images posted in enabled channels and flags
    potentially inappropriate content.
    Keywords and settings are stored per-server.
    '''

    def __init__(self, bot):
        self.bot = bot
        self.keywords_cache: dict[int, list[tuple[str, str | None]]] = {}   # guild_id → [(keyword, category)]
        self.settings_cache: dict[int, dict[str, str]] = {}                 # guild_id → {key: value}

    # ─── Per-guild keyword DB helpers ────────────────────────────────────

    async def seed_keywords(self, guild_id: int):
        """Seed the default keywords for a guild if it has none."""
        rows = []
        for category, keywords in DEFAULT_IMAGEMOD_FLAGGED_KEYWORDS.items():
            for kw in keywords:
                rows.append((guild_id, kw, category))
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            await con.executemany(
                'INSERT OR IGNORE INTO keywords (SERVER_ID, KEYWORD, CATEGORY) VALUES (?, ?, ?)',
                rows
            )
            await con.commit()

    async def load_keywords(self, guild_id: int) -> list[tuple[str, str | None]]:
        """Load flagged keywords for a guild from the DB and refresh cache. Seeds defaults if empty."""
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            async with con.execute(
                'SELECT KEYWORD, CATEGORY FROM keywords WHERE SERVER_ID = ? ORDER BY CATEGORY, KEYWORD',
                (guild_id,)
            ) as cursor:
                rows = await cursor.fetchall()
        if not rows:
            await self.seed_keywords(guild_id)
            async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
                async with con.execute(
                    'SELECT KEYWORD, CATEGORY FROM keywords WHERE SERVER_ID = ? ORDER BY CATEGORY, KEYWORD',
                    (guild_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
        self.keywords_cache[guild_id] = rows
        return rows

    async def get_keywords(self, guild_id: int) -> list[tuple[str, str | None]]:
        """Return cached keywords for a guild, loading from DB if not cached."""
        if guild_id not in self.keywords_cache:
            await self.load_keywords(guild_id)
        return self.keywords_cache[guild_id]

    async def get_keyword_list(self, guild_id: int) -> list[str]:
        """Return just the keyword strings for a guild."""
        keywords = await self.get_keywords(guild_id)
        return [kw for kw, _ in keywords]

    # ─── Per-guild settings DB helpers ───────────────────────────────────

    async def load_guild_settings(self, guild_id: int) -> dict[str, str]:
        """Load per-guild settings (e.g. classification_threshold)."""
        settings: dict[str, str] = {}
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            async with con.execute(
                'SELECT KEY, VALUE FROM settings WHERE SERVER_ID = ?',
                (guild_id,)
            ) as cur:
                async for row in cur:
                    settings[row[0]] = row[1]
        self.settings_cache[guild_id] = settings
        return settings

    async def get_guild_settings(self, guild_id: int) -> dict[str, str]:
        """Return cached guild settings, loading if not cached."""
        if guild_id not in self.settings_cache:
            await self.load_guild_settings(guild_id)
        return self.settings_cache[guild_id]

    async def get_guild_threshold(self, guild_id: int) -> float:
        """Return the classification threshold for a guild."""
        settings = await self.get_guild_settings(guild_id)
        return float(settings.get('classification_threshold', str(IMAGEMOD_CLASSIFICATION_THRESHOLD)))

    async def set_guild_setting(self, guild_id: int, key: str, value: str):
        """Write a single per-guild setting to DB and refresh cache."""
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            await con.execute(
                'INSERT INTO settings (SERVER_ID, KEY, VALUE) VALUES (?, ?, ?) '
                'ON CONFLICT(SERVER_ID, KEY) DO UPDATE SET VALUE = excluded.VALUE',
                (guild_id, key, value)
            )
            await con.commit()
        await self.load_guild_settings(guild_id)

    # ─── Log channel DB helpers ──────────────────────────────────────────

    async def get_log_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Get the configured log channel for a guild, falling back to 'imagemod-log' by name."""
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            async with con.execute(
                'SELECT CHANNEL_ID FROM log_channels WHERE SERVER_ID = ?',
                (guild.id,)
            ) as cursor:
                row = await cursor.fetchone()
        if row:
            channel = guild.get_channel(row[0])
            if channel:
                return channel
        # Fallback: look for a channel named 'imagemod-log'
        return discord.utils.get(guild.text_channels, name='imagemod-log')

    @commands.Cog.listener()
    async def on_ready(self):
        print('Image screening module online')
        # Pre-load both models in the background
        asyncio.create_task(model_manager.ensure_all_loaded())

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

        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('SELECT enabled FROM imagemod WHERE server_id = ?', (guild_id,)) as cursor:
                result = await cursor.fetchone()
                enabled = result is not None and result[0]

        if not enabled:
            return

        threshold = await self.get_guild_threshold(guild_id)

        # Screen every image attachment
        for attachment in image_attachments:
            result = await self.screen_image(attachment.url, guild_id, threshold)
            if result is None:
                continue

            log_channel = await self.get_log_channel(message.guild)
            flagged = result['flagged']

            # Build description parts
            desc_parts = []
            if result.get('caption'):
                desc_parts.append(f'**Caption:** {result["caption"]}')
            if result.get('labels'):
                label_str = ', '.join(f'{l["label"]} ({l["score"]:.1%})' for l in result['labels'])
                desc_parts.append(f'**Classification:** {label_str}')
            if result.get('flagged_keywords'):
                desc_parts.append(f'**Flagged keywords:** {", ".join(result["flagged_keywords"])}')
            desc_parts.append(f'**Author:** {message.author.mention}')
            desc_parts.append(f'**Channel:** {message.channel.mention}')
            desc_parts.append(f'**[Jump to message]({message.jump_url})**')

            # # Build footer showing active models
            # model_names = []
            # if model_manager.captioning_enabled and model_manager.captioning_model_name:
            #     model_names.append(model_manager.captioning_model_name)
            # if model_manager.classification_enabled and model_manager.classification_model_name:
            #     model_names.append(model_manager.classification_model_name)
            # footer = ' + '.join(model_names) + f' • {BOTVERSION}' if model_names else BOTVERSION

            if flagged:
                embed = discord.Embed(
                    title='⚠ Flagged Image Detected',
                    description='\n'.join(desc_parts),
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=attachment.url)
                embed.set_footer(text=BOTVERSION)

                view = ImageActionView(member=message.author, flagged_message=message)

                await log_channel.send(embed=embed, view=view)

            # else:
            #     embed = discord.Embed(
            #         title='✅ Image Screened — No Flags',
            #         description='\n'.join(desc_parts),
            #         color=discord.Color.green()
            #     )
            #     embed.set_thumbnail(url=attachment.url)
            #     embed.set_footer(text=BOTVERSION)

            #     await log_channel.send(embed=embed)

    # ─── Manual describe command ─────────────────────────────────────────

    @commands.command(name='describe')
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
            guild_id = ctx.guild.id
            threshold = await self.get_guild_threshold(guild_id)
            result = await self.screen_image(attachment.url, guild_id, threshold)

        if result:
            desc_parts = []
            if result.get('caption'):
                desc_parts.append(f'**Caption:** {result["caption"]}')
            if result.get('labels'):
                label_str = ', '.join(f'{l["label"]} ({l["score"]:.1%})' for l in result['labels'])
                desc_parts.append(f'**Classification:** {label_str}')

            # model_names = []
            # if model_manager.captioning_enabled and model_manager.captioning_model_name:
            #     model_names.append(model_manager.captioning_model_name)
            # if model_manager.classification_enabled and model_manager.classification_model_name:
            #     model_names.append(model_manager.classification_model_name)

            embed = discord.Embed(
                title='Image Description',
                description='\n'.join(desc_parts) if desc_parts else 'No output',
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=attachment.url)
            embed.set_footer(text=BOTVERSION)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await ctx.reply(
                'Could not describe that image. The model may still be loading — try again shortly.',
                mention_author=False, delete_after=MSG_DEL_DELAY
            )

    # ─── Model status command ────────────────────────────────────────────

    @commands.command(name='screeninfo')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def screen_info(self, ctx):
        '''
        Show the current image screening model status and configuration.
        '''
        guild_id = ctx.guild.id
        threshold = await self.get_guild_threshold(guild_id)

        embed = discord.Embed(title='Image Screening Info', color=discord.Color.blurple())

        # Captioning model
        cap_status = '✅ Loaded' if model_manager.captioning_ready else ('⏳ Loading...' if model_manager.captioning_loading else '❌ Not loaded')
        cap_state = f'**{model_manager.captioning_model_name or "Not set"}**\n'
        cap_state += f'Status: {cap_status}'
        embed.add_field(name='📝 Captioning Model', value=cap_state, inline=False)

        # Classification model
        cls_status = '✅ Loaded' if model_manager.classification_ready else ('⏳ Loading...' if model_manager.classification_loading else '❌ Not loaded')
        cls_state = f'**{model_manager.classification_model_name or "Not set"}**\n'
        cls_state += f'Status: {cls_status}\n'
        cls_state += f'Threshold: {threshold:.0%}'
        embed.add_field(name='🏷️ Classification Model', value=cls_state, inline=False)

        # Keywords
        keywords = await self.get_keyword_list(guild_id)
        kw_display = ', '.join(keywords[:50]) or 'None'
        if len(keywords) > 50:
            kw_display += f' ... and {len(keywords) - 50} more'
        embed.add_field(name='Flagged Keywords', value=kw_display, inline=False)

        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    # ─── Internal helpers ────────────────────────────────────────────────

    async def screen_image(self, url: str, guild_id: int,
                           threshold: float = 0.5) -> dict | None:
        """
        Download an image and run it through both models.
        Both models always run if loaded; the on/off gate is in permissions_data.
        Returns a dict with keys:
          - 'flagged'          : bool  (True if EITHER model flags the image)
          - 'caption'          : str | None        (from captioning model)
          - 'flagged_keywords' : list[str] | None  (from captioning model)
          - 'labels'           : list[dict] | None (from classification model, [{label, score}, ...])
        Returns None on total failure.
        """
        await model_manager.ensure_all_loaded()
        if not model_manager.captioning_ready and not model_manager.classification_ready:
            return None

        try:
            loop = asyncio.get_event_loop()
            image_bytes = await loop.run_in_executor(None, lambda: requests.get(url).content)

            from PIL import Image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

            # Run both models concurrently
            caption_task = None
            classify_task = None

            if model_manager.captioning_ready:
                caption_task = asyncio.create_task(self.run_captioning(image, loop, guild_id))
            if model_manager.classification_ready:
                classify_task = asyncio.create_task(self.run_classification(image, loop, threshold))

            caption_result = await caption_task if caption_task else None
            classify_result = await classify_task if classify_task else None

            # Merge results
            flagged = False
            caption = None
            flagged_keywords = None
            labels = None

            if caption_result:
                caption = caption_result.get('caption')
                flagged_keywords = caption_result.get('flagged_keywords')
                if caption_result.get('flagged'):
                    flagged = True

            if classify_result:
                labels = classify_result.get('labels')
                if classify_result.get('flagged'):
                    flagged = True

            return {
                'flagged': flagged,
                'caption': caption,
                'flagged_keywords': flagged_keywords,
                'labels': labels,
            }
        except Exception:
            return None

    async def run_captioning(self, image, loop, guild_id: int) -> dict:
        """Run a captioning model and check caption against the guild's flagged keywords."""
        processor = model_manager.captioning_processor
        model = model_manager.captioning_model

        def run_inference():
            inputs = processor(images=image, return_tensors='pt')
            output = model.generate(**inputs, max_new_tokens=5000, num_beams=1, early_stopping=False)
            return processor.decode(output[0], skip_special_tokens=True)

        caption = await loop.run_in_executor(None, run_inference)
        caption = caption.strip() if caption else ''
        flagged_kws = await self.check_flagged(caption, guild_id)
        return {
            'flagged': bool(flagged_kws),
            'caption': caption,
            'flagged_keywords': flagged_kws,
        }

    async def run_classification(self, image, loop, threshold: float) -> dict:
        """Run a classification model and flag based on the guild's threshold."""
        pipe = model_manager.classification_pipeline

        def run_inference():
            return pipe(image)

        results = await loop.run_in_executor(None, run_inference)
        # results = [{'label': 'nsfw', 'score': 0.95}, {'label': 'normal', 'score': 0.05}]

        safe_labels = {'normal', 'safe', 'sfw'}
        flagged_labels = [
            r for r in results
            if r['label'].lower() not in safe_labels and r['score'] >= threshold
        ]
        return {
            'flagged': bool(flagged_labels),
            'labels': results,
        }

    async def check_flagged(self, description: str, guild_id: int) -> list[str]:
        """Check if the description contains any flagged keywords for the guild."""
        description_lower = description.lower()
        keywords = await self.get_keyword_list(guild_id)
        return [kw for kw in keywords if kw.lower() in description_lower]

    # ─── Admin keyword management commands ───────────────────────────────

    @commands.group(name='keyword', aliases=['kw'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def keyword(self, ctx):
        '''
        Manage flagged image keywords. Use subcommands: add, remove, list, clear.
        '''
        await ctx.send_help(ctx.command)

    @keyword.command(name='add')
    @commands.has_permissions(administrator=True)
    async def keyword_add(self, ctx, category: str = 'general', *, keywords: str = None):
        '''
        Add one or more flagged keywords.
        Usage: keyword add <category> <keyword1, keyword2, ...>
        Example: keyword add sexual nude, naked, topless
        '''
        if keywords is None:
            await ctx.reply(
                f'Usage: `{COMMAND_PREFIX}keyword add <category> <keyword1, keyword2, ...>`',
                mention_author=False, delete_after=MSG_DEL_DELAY
            )
            return

        kw_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
        if not kw_list:
            await ctx.reply('No valid keywords provided.', mention_author=False, delete_after=MSG_DEL_DELAY)
            return

        added = []
        duplicates = []
        guild_id = ctx.guild.id
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            for kw in kw_list:
                try:
                    await con.execute(
                        'INSERT INTO keywords (SERVER_ID, KEYWORD, CATEGORY) VALUES (?, ?, ?)',
                        (guild_id, kw, category.lower())
                    )
                    added.append(kw)
                except aiosqlite.IntegrityError:
                    duplicates.append(kw)
            await con.commit()

        # Refresh cache
        await self.load_keywords(guild_id)

        parts = []
        if added:
            parts.append(f'**Added ({category}):** {", ".join(added)}')
        if duplicates:
            parts.append(f'**Already exists:** {", ".join(duplicates)}')
        embed = discord.Embed(
            title='Keyword Update',
            description='\n'.join(parts),
            color=discord.Color.green() if added else discord.Color.orange()
        )
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    @keyword.command(name='remove', aliases=['rm'])
    @commands.has_permissions(administrator=True)
    async def keyword_remove(self, ctx, *, keywords: str = None):
        '''
        Remove one or more flagged keywords.
        Usage: keyword remove <keyword1, keyword2, ...>
        '''
        if keywords is None:
            await ctx.reply(
                f'Usage: `{COMMAND_PREFIX}keyword remove <keyword1, keyword2, ...>`',
                mention_author=False, delete_after=MSG_DEL_DELAY
            )
            return

        kw_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
        if not kw_list:
            await ctx.reply('No valid keywords provided.', mention_author=False, delete_after=MSG_DEL_DELAY)
            return

        removed = []
        not_found = []
        guild_id = ctx.guild.id
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            for kw in kw_list:
                cursor = await con.execute(
                    'DELETE FROM keywords WHERE SERVER_ID = ? AND KEYWORD = ?',
                    (guild_id, kw)
                )
                if cursor.rowcount > 0:
                    removed.append(kw)
                else:
                    not_found.append(kw)
            await con.commit()

        # Refresh cache
        await self.load_keywords(guild_id)

        parts = []
        if removed:
            parts.append(f'**Removed:** {", ".join(removed)}')
        if not_found:
            parts.append(f'**Not found:** {", ".join(not_found)}')
        embed = discord.Embed(
            title='Keyword Update',
            description='\n'.join(parts),
            color=discord.Color.green() if removed else discord.Color.orange()
        )
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    @keyword.command(name='list')
    @commands.has_permissions(administrator=True)
    async def keyword_list(self, ctx, category: str = None):
        '''
        List all flagged keywords, optionally filtered by category.
        Usage: keyword list [category]
        '''
        keywords = await self.load_keywords(ctx.guild.id)

        if category:
            keywords = [(kw, cat) for kw, cat in keywords if cat and cat.lower() == category.lower()]

        if not keywords:
            await ctx.reply('No keywords found.', mention_author=False, delete_after=MSG_DEL_DELAY)
            return

        # Group by category
        grouped: dict[str, list[str]] = {}
        for kw, cat in keywords:
            cat_name = cat or 'uncategorized'
            grouped.setdefault(cat_name, []).append(kw)

        embed = discord.Embed(title='Flagged Keywords', color=discord.Color.blurple())
        for cat_name, kws in grouped.items():
            embed.add_field(
                name=cat_name.capitalize(),
                value=', '.join(kws),
                inline=False
            )
        embed.set_footer(text=f'{len(keywords)} keywords total • {BOTVERSION}')
        await ctx.reply(embed=embed, mention_author=False)

    @keyword.command(name='clear', hidden=True)
    @commands.is_owner()
    async def keyword_clear(self, ctx, category: str = None):
        '''
        Clear all flagged keywords, or all keywords in a specific category.
        Usage: keyword clear [category]
        '''
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            guild_id = ctx.guild.id
            if category:
                await con.execute(
                    'DELETE FROM keywords WHERE SERVER_ID = ? AND CATEGORY = ?',
                    (guild_id, category.lower())
                )
                msg = f'All keywords in category **{category}** cleared.'
            else:
                await con.execute('DELETE FROM keywords WHERE SERVER_ID = ?', (guild_id,))
                msg = 'All flagged keywords cleared.'
            await con.commit()

        # Refresh cache
        await self.load_keywords(guild_id)

        embed = discord.Embed(
            title='Keywords Cleared',
            description=msg,
            color=discord.Color.red()
        )
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    # ─── Model management command ────────────────────────────────────────

    @commands.group(name='setmodel', invoke_without_command=True, hidden=True)
    @commands.is_owner()
    async def setmodel(self, ctx, model_type: str = None, *, model_name: str = None):
        '''
        Switch a captioning or classification model (global, bot-owner only).
        Usage: setmodel <captioning|classification> <huggingface_model_name>
        Example: setmodel classification Falconsai/nsfw_image_detection
        Example: setmodel captioning Salesforce/blip-image-captioning-large
        Omit arguments to see both models.
        '''
        if model_type is None:
            # Show current status of both models
            await model_manager.load_global_settings()
            threshold = await self.get_guild_threshold(ctx.guild.id)

            embed = discord.Embed(title='Current Models', color=discord.Color.blurple())

            cap_status = '✅ Loaded' if model_manager.captioning_ready else '❌ Not loaded'
            cap_val = f'**{model_manager.captioning_model_name or "Not set"}**\n'
            cap_val += f'Status: {cap_status}'
            embed.add_field(name='📝 Captioning', value=cap_val, inline=False)

            cls_status = '✅ Loaded' if model_manager.classification_ready else '❌ Not loaded'
            cls_val = f'**{model_manager.classification_model_name or "Not set"}**\n'
            cls_val += f'Status: {cls_status}\n'
            cls_val += f'Threshold (this server): {threshold:.0%}'
            embed.add_field(name='🏷️ Classification', value=cls_val, inline=False)

            embed.set_footer(text=BOTVERSION)
            await ctx.reply(embed=embed, mention_author=False)
            return

        if model_type not in ('captioning', 'classification'):
            await ctx.reply(
                f'Type must be `captioning` or `classification`.\n'
                f'Usage: `{COMMAND_PREFIX}setmodel <captioning|classification> <model_name>`',
                mention_author=False, delete_after=MSG_DEL_DELAY
            )
            return

        if model_name is None:
            await ctx.reply(
                f'Usage: `{COMMAND_PREFIX}setmodel {model_type} <huggingface_model_name>`',
                mention_author=False, delete_after=MSG_DEL_DELAY
            )
            return

        # Save to DB (global, SERVER_ID=0)
        db_key = 'captioning_model' if model_type == 'captioning' else 'classification_model'
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            await con.execute(
                'INSERT INTO settings (SERVER_ID, KEY, VALUE) VALUES (0, ?, ?) '
                'ON CONFLICT(SERVER_ID, KEY) DO UPDATE SET VALUE = excluded.VALUE',
                (db_key, model_name)
            )
            await con.commit()

        # Reload that specific model
        embed = discord.Embed(
            title='Model Switching...',
            description=f'Downloading and loading **{model_name}** (`{model_type}`)...\nThis may take a minute.',
            color=discord.Color.orange()
        )
        embed.set_footer(text=BOTVERSION)
        status_msg = await ctx.reply(embed=embed, mention_author=False)

        await model_manager.load_global_settings()
        if model_type == 'captioning':
            await model_manager.reload_captioning()
            success = model_manager.captioning_ready
        else:
            await model_manager.reload_classification()
            success = model_manager.classification_ready

        if success:
            embed = discord.Embed(
                title='Model Updated ✅',
                description=f'**{model_type.capitalize()}** model set to **{model_name}**.',
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title='Model Failed ❌',
                description=f'Failed to load **{model_name}**. Check the model name.\n'
                            f'The previous {model_type} model has been unloaded.',
                color=discord.Color.red()
            )
        embed.set_footer(text=BOTVERSION)
        await status_msg.edit(embed=embed)

    @setmodel.command(name='threshold')
    @commands.has_permissions(administrator=True)
    async def setmodel_threshold(self, ctx, threshold: float = None):
        '''
        Set the classification confidence threshold for this server (0.0 - 1.0).
        Images with a non-safe label scoring above this are flagged.
        Usage: setmodel threshold 0.7
        '''
        guild_id = ctx.guild.id
        current_threshold = await self.get_guild_threshold(guild_id)

        if threshold is None:
            await ctx.reply(
                f'Current classification threshold: **{current_threshold:.0%}**\n'
                f'Usage: `{COMMAND_PREFIX}setmodel threshold <0.0 - 1.0>`',
                mention_author=False
            )
            return

        if not 0.0 <= threshold <= 1.0:
            await ctx.reply('Threshold must be between 0.0 and 1.0.', mention_author=False, delete_after=MSG_DEL_DELAY)
            return

        await self.set_guild_setting(guild_id, 'classification_threshold', str(threshold))

        embed = discord.Embed(
            title='Threshold Updated',
            description=f'Classification threshold set to **{threshold:.0%}** for this server.',
            color=discord.Color.green()
        )
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    # ─── Log channel command ────────────────────────────────────────────

    @commands.command(name='setlogchannel', aliases=['slc'])
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel = None):
        '''
        Set the channel where image screening results are logged.
        Usage: setlogchannel #channel
        Omit the channel to see the current setting.
        '''
        guild_id = ctx.guild.id

        if channel is None:
            # Show current setting
            current = await self.get_log_channel(ctx.guild)
            if current:
                await ctx.reply(
                    f'Current imagemod log channel: {current.mention}',
                    mention_author=False
                )
            else:
                await ctx.reply(
                    'No log channel set. Falling back to a channel named `imagemod-log`.',
                    mention_author=False
                )
            return

        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            await con.execute(
                'INSERT INTO log_channels (SERVER_ID, CHANNEL_ID) VALUES (?, ?) '
                'ON CONFLICT(SERVER_ID) DO UPDATE SET CHANNEL_ID = excluded.CHANNEL_ID',
                (guild_id, channel.id)
            )
            await con.commit()

        embed = discord.Embed(
            title='Log Channel Updated',
            description=f'Image screening logs will now be sent to {channel.mention}.',
            color=discord.Color.green()
        )
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)



async def setup(bot):
    await bot.add_cog(Imagemod(bot))
