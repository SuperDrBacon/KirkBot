import asyncio
import io

import aiosqlite
import discord
import requests
from discord.ext import commands

from cogs.utils.constants import (BOTVERSION, COMMAND_PREFIX,
                                  IMAGEMOD_DATABASE, MSG_DEL_DELAY, OWNER_ID,
                                  PERMISSIONS_DATABASE)

# ─── Dynamic model manager ──────────────────────────────────────────────

class _ModelManager:
    """
    Manages two HuggingFace models that can run simultaneously:
      - captioning      : image-to-text (e.g. BLIP) → generates a caption → keyword flagging
      - classification  : image-classification (e.g. Falconsai/nsfw_image_detection) → label + score
    Either or both can be enabled/disabled independently.
    """
    def __init__(self):
        # Captioning model
        self.captioning_model_name: str | None = None
        self.captioning_enabled: bool = True
        self.captioning_processor = None
        self.captioning_model = None
        self.captioning_ready: bool = False
        self.captioning_loading: bool = False

        # Classification model
        self.classification_model_name: str | None = None
        self.classification_enabled: bool = True
        self.classification_pipeline = None
        self.classification_ready: bool = False
        self.classification_loading: bool = False
        self.threshold: float = 0.5

    async def load_settings(self):
        """Read model config from the imagemod database."""
        settings: dict[str, str] = {}
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            async with con.execute('SELECT KEY, VALUE FROM settings') as cur:
                async for row in cur:
                    settings[row[0]] = row[1]
        self.captioning_model_name = settings.get('captioning_model')
        self.captioning_enabled = settings.get('captioning_enabled', '1') == '1'
        self.classification_model_name = settings.get('classification_model')
        self.classification_enabled = settings.get('classification_enabled', '1') == '1'
        self.threshold = float(settings.get('classification_threshold', '0.5'))

    # ── Captioning loader ────────────────────────────────────────────

    def load_captioning_sync(self, name: str):
        from transformers import BlipForConditionalGeneration, BlipProcessor
        processor = BlipProcessor.from_pretrained(name)
        model = BlipForConditionalGeneration.from_pretrained(name)
        return processor, model

    async def ensure_captioning_loaded(self):
        if self.captioning_ready or self.captioning_loading or not self.captioning_enabled:
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
        if self.classification_ready or self.classification_loading or not self.classification_enabled:
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
        await self.load_settings()
        tasks = []
        if self.captioning_enabled and not self.captioning_ready:
            tasks.append(self.ensure_captioning_loaded())
        if self.classification_enabled and not self.classification_ready:
            tasks.append(self.ensure_classification_loaded())
        if tasks:
            await asyncio.gather(*tasks)


_manager = _ModelManager()


class Imagemod(commands.Cog):
    '''
    Image screening module using a local HuggingFace image-to-text model.
    Automatically describes images posted in enabled channels and flags
    potentially inappropriate content.
    '''
    def __init__(self, bot):
        self.bot = bot
        self._keywords_cache: list[tuple[str, str | None]] = []  # (keyword, category)

    # ─── Keyword DB helpers ──────────────────────────────────────────────

    async def load_keywords(self) -> list[tuple[str, str | None]]:
        """Load flagged keywords from the imagemod database and refresh cache."""
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            async with con.execute('SELECT KEYWORD, CATEGORY FROM keywords ORDER BY CATEGORY, KEYWORD') as cursor:
                rows = await cursor.fetchall()
        self._keywords_cache = rows
        return rows

    async def get_keywords(self) -> list[tuple[str, str | None]]:
        """Return cached keywords, loading from DB if cache is empty."""
        if not self._keywords_cache:
            await self.load_keywords()
        return self._keywords_cache

    async def _get_keyword_list(self) -> list[str]:
        """Return just the keyword strings."""
        keywords = await self.get_keywords()
        return [kw for kw, _ in keywords]

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
        # Pre-load keywords cache
        await self.load_keywords()
        # Pre-load both models in the background
        asyncio.create_task(_manager.ensure_all_loaded())

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
                'SELECT enabled FROM imagemod WHERE server_id = ? AND channel_id = ?',
                (guild_id, channel_id)
            ) as cursor:
                result = await cursor.fetchone()
                enabled = result is not None and result[0]

        if not enabled:
            return

        # Screen every image attachment
        for attachment in image_attachments:
            result = await self.screen_image(attachment.url)
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

            # Build footer showing active models
            model_names = []
            if _manager.captioning_enabled and _manager.captioning_model_name:
                model_names.append(_manager.captioning_model_name)
            if _manager.classification_enabled and _manager.classification_model_name:
                model_names.append(_manager.classification_model_name)
            footer = ' + '.join(model_names) + f' • {BOTVERSION}' if model_names else BOTVERSION

            if flagged:
                embed = discord.Embed(
                    title='⚠ Flagged Image Detected',
                    description='\n'.join(desc_parts),
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=attachment.url)
                embed.set_footer(text=footer)

                if log_channel:
                    await log_channel.send(embed=embed)
                else:
                    await message.channel.send(embed=embed, delete_after=30)
            else:
                embed = discord.Embed(
                    title='✅ Image Screened — No Flags',
                    description='\n'.join(desc_parts),
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=attachment.url)
                embed.set_footer(text=footer)

                if log_channel:
                    await log_channel.send(embed=embed)
                

    # ─── Manual describe command ─────────────────────────────────────────

    @commands.command(name='describe', aliases=['imgdesc'])
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
            result = await self.screen_image(attachment.url)

        if result:
            desc_parts = []
            if result.get('caption'):
                desc_parts.append(f'**Caption:** {result["caption"]}')
            if result.get('labels'):
                label_str = ', '.join(f'{l["label"]} ({l["score"]:.1%})' for l in result['labels'])
                desc_parts.append(f'**Classification:** {label_str}')

            model_names = []
            if _manager.captioning_enabled and _manager.captioning_model_name:
                model_names.append(_manager.captioning_model_name)
            if _manager.classification_enabled and _manager.classification_model_name:
                model_names.append(_manager.classification_model_name)

            embed = discord.Embed(
                title='Image Description',
                description='\n'.join(desc_parts) if desc_parts else 'No output',
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=attachment.url)
            embed.set_footer(text=f'Models: {" + ".join(model_names)}')
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
        embed = discord.Embed(title='Image Screening Info', color=discord.Color.blurple())

        # Captioning model
        cap_status = '✅ Loaded' if _manager.captioning_ready else ('⏳ Loading...' if _manager.captioning_loading else '❌ Not loaded')
        cap_state = f'**{_manager.captioning_model_name or "Not set"}**\n'
        cap_state += f'Status: {cap_status}\n'
        cap_state += f'Enabled: {"Yes" if _manager.captioning_enabled else "No"}'
        embed.add_field(name='📝 Captioning Model', value=cap_state, inline=False)

        # Classification model
        cls_status = '✅ Loaded' if _manager.classification_ready else ('⏳ Loading...' if _manager.classification_loading else '❌ Not loaded')
        cls_state = f'**{_manager.classification_model_name or "Not set"}**\n'
        cls_state += f'Status: {cls_status}\n'
        cls_state += f'Enabled: {"Yes" if _manager.classification_enabled else "No"}\n'
        cls_state += f'Threshold: {_manager.threshold:.0%}'
        embed.add_field(name='🏷️ Classification Model', value=cls_state, inline=False)

        # Keywords (only relevant for captioning)
        if _manager.captioning_enabled:
            keywords = await self._get_keyword_list()
            kw_display = ', '.join(keywords[:50]) or 'None'
            if len(keywords) > 50:
                kw_display += f' ... and {len(keywords) - 50} more'
            embed.add_field(name='Flagged Keywords', value=kw_display, inline=False)

        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    # ─── Internal helpers ────────────────────────────────────────────────

    async def screen_image(self, url: str) -> dict | None:
        """
        Download an image and run it through all enabled models.
        Returns a dict with keys:
          - 'flagged'          : bool  (True if EITHER model flags the image)
          - 'caption'          : str | None        (from captioning model)
          - 'flagged_keywords' : list[str] | None  (from captioning model)
          - 'labels'           : list[dict] | None (from classification model, [{label, score}, ...])
        Returns None on total failure.
        """
        await _manager.ensure_all_loaded()
        if not _manager.captioning_ready and not _manager.classification_ready:
            return None

        try:
            loop = asyncio.get_event_loop()
            image_bytes = await loop.run_in_executor(None, lambda: requests.get(url).content)

            from PIL import Image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

            # Run enabled models concurrently
            caption_task = None
            classify_task = None

            if _manager.captioning_enabled and _manager.captioning_ready:
                caption_task = asyncio.create_task(self._run_captioning(image, loop))
            if _manager.classification_enabled and _manager.classification_ready:
                classify_task = asyncio.create_task(self._run_classification(image, loop))

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

    async def _run_captioning(self, image, loop) -> dict:
        """Run a captioning model and check caption against flagged keywords."""
        processor = _manager.captioning_processor
        model = _manager.captioning_model

        def run_inference():
            inputs = processor(images=image, return_tensors='pt')
            output = model.generate(**inputs, max_new_tokens=5000, num_beams=1, early_stopping=False)
            return processor.decode(output[0], skip_special_tokens=True)

        caption = await loop.run_in_executor(None, run_inference)
        caption = caption.strip() if caption else ''
        flagged_kws = await self.check_flagged(caption)
        return {
            'flagged': bool(flagged_kws),
            'caption': caption,
            'flagged_keywords': flagged_kws,
        }

    async def _run_classification(self, image, loop) -> dict:
        """Run a classification model and flag based on threshold."""
        pipe = _manager.classification_pipeline
        threshold = _manager.threshold

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

    async def check_flagged(self, description: str) -> list[str]:
        """Check if the description contains any flagged keywords from the database."""
        description_lower = description.lower()
        keywords = await self._get_keyword_list()
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
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            for kw in kw_list:
                try:
                    await con.execute(
                        'INSERT INTO keywords (KEYWORD, CATEGORY) VALUES (?, ?)',
                        (kw, category.lower())
                    )
                    added.append(kw)
                except aiosqlite.IntegrityError:
                    duplicates.append(kw)
            await con.commit()

        # Refresh cache
        await self.load_keywords()

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

    @keyword.command(name='remove', aliases=['rm', 'delete', 'del'])
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
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            for kw in kw_list:
                cursor = await con.execute('DELETE FROM keywords WHERE KEYWORD = ?', (kw,))
                if cursor.rowcount > 0:
                    removed.append(kw)
                else:
                    not_found.append(kw)
            await con.commit()

        # Refresh cache
        await self.load_keywords()

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

    @keyword.command(name='list', aliases=['ls', 'show'])
    @commands.has_permissions(administrator=True)
    async def keyword_list(self, ctx, category: str = None):
        '''
        List all flagged keywords, optionally filtered by category.
        Usage: keyword list [category]
        '''
        keywords = await self.load_keywords()

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

    @keyword.command(name='clear')
    @commands.has_permissions(administrator=True)
    async def keyword_clear(self, ctx, category: str = None):
        '''
        Clear all flagged keywords, or all keywords in a specific category.
        Usage: keyword clear [category]
        '''
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            if category:
                await con.execute('DELETE FROM keywords WHERE CATEGORY = ?', (category.lower(),))
                msg = f'All keywords in category **{category}** cleared.'
            else:
                await con.execute('DELETE FROM keywords')
                msg = 'All flagged keywords cleared.'
            await con.commit()

        # Refresh cache
        await self.load_keywords()

        embed = discord.Embed(
            title='Keywords Cleared',
            description=msg,
            color=discord.Color.red()
        )
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    # ─── Model management command ────────────────────────────────────────

    @commands.group(name='setmodel', aliases=['model'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def setmodel(self, ctx, model_type: str = None, *, model_name: str = None):
        '''
        Switch a captioning or classification model.
        Usage: setmodel <captioning|classification> <huggingface_model_name>
        Example: setmodel classification Falconsai/nsfw_image_detection
        Example: setmodel captioning Salesforce/blip-image-captioning-large
        Omit arguments to see both models.
        '''
        if model_type is None:
            # Show current status of both models
            await _manager.load_settings()
            embed = discord.Embed(title='Current Models', color=discord.Color.blurple())

            cap_status = '✅ Loaded' if _manager.captioning_ready else '❌ Not loaded'
            cap_val = f'**{_manager.captioning_model_name or "Not set"}**\n'
            cap_val += f'Status: {cap_status}\n'
            cap_val += f'Enabled: {"Yes" if _manager.captioning_enabled else "No"}'
            embed.add_field(name='📝 Captioning', value=cap_val, inline=False)

            cls_status = '✅ Loaded' if _manager.classification_ready else '❌ Not loaded'
            cls_val = f'**{_manager.classification_model_name or "Not set"}**\n'
            cls_val += f'Status: {cls_status}\n'
            cls_val += f'Enabled: {"Yes" if _manager.classification_enabled else "No"}\n'
            cls_val += f'Threshold: {_manager.threshold:.0%}'
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

        # Save to DB
        db_key = 'captioning_model' if model_type == 'captioning' else 'classification_model'
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            await con.execute(
                'INSERT INTO settings (KEY, VALUE) VALUES (?, ?) '
                'ON CONFLICT(KEY) DO UPDATE SET VALUE = excluded.VALUE',
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

        await _manager.load_settings()
        if model_type == 'captioning':
            await _manager.reload_captioning()
            success = _manager.captioning_ready
        else:
            await _manager.reload_classification()
            success = _manager.classification_ready

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

    @setmodel.command(name='enable', aliases=['on'])
    @commands.has_permissions(administrator=True)
    async def setmodel_enable(self, ctx, model_type: str = None):
        '''
        Enable a model type.
        Usage: setmodel enable <captioning|classification>
        '''
        if model_type not in ('captioning', 'classification'):
            await ctx.reply(
                f'Usage: `{COMMAND_PREFIX}setmodel enable <captioning|classification>`',
                mention_author=False, delete_after=MSG_DEL_DELAY
            )
            return

        db_key = f'{model_type}_enabled'
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            await con.execute(
                'INSERT INTO settings (KEY, VALUE) VALUES (?, ?) '
                'ON CONFLICT(KEY) DO UPDATE SET VALUE = excluded.VALUE',
                (db_key, '1')
            )
            await con.commit()

        if model_type == 'captioning':
            _manager.captioning_enabled = True
            asyncio.create_task(_manager.ensure_captioning_loaded())
        else:
            _manager.classification_enabled = True
            asyncio.create_task(_manager.ensure_classification_loaded())

        embed = discord.Embed(
            title=f'{model_type.capitalize()} Model Enabled ✅',
            description=f'The {model_type} model is now enabled and will be used for screening.',
            color=discord.Color.green()
        )
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    @setmodel.command(name='disable', aliases=['off'])
    @commands.has_permissions(administrator=True)
    async def setmodel_disable(self, ctx, model_type: str = None):
        '''
        Disable a model type (the other model will still run).
        Usage: setmodel disable <captioning|classification>
        '''
        if model_type not in ('captioning', 'classification'):
            await ctx.reply(
                f'Usage: `{COMMAND_PREFIX}setmodel disable <captioning|classification>`',
                mention_author=False, delete_after=MSG_DEL_DELAY
            )
            return

        db_key = f'{model_type}_enabled'
        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            await con.execute(
                'INSERT INTO settings (KEY, VALUE) VALUES (?, ?) '
                'ON CONFLICT(KEY) DO UPDATE SET VALUE = excluded.VALUE',
                (db_key, '0')
            )
            await con.commit()

        if model_type == 'captioning':
            _manager.captioning_enabled = False
        else:
            _manager.classification_enabled = False

        embed = discord.Embed(
            title=f'{model_type.capitalize()} Model Disabled',
            description=f'The {model_type} model is now disabled.',
            color=discord.Color.orange()
        )
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    @setmodel.command(name='threshold')
    @commands.has_permissions(administrator=True)
    async def setmodel_threshold(self, ctx, threshold: float = None):
        '''
        Set the confidence threshold for the classification model (0.0 - 1.0).
        Images with a non-safe label scoring above this are flagged.
        Usage: setmodel threshold 0.7
        '''
        if threshold is None:
            await ctx.reply(
                f'Current classification threshold: **{_manager.threshold:.0%}**\n'
                f'Usage: `{COMMAND_PREFIX}setmodel threshold <0.0 - 1.0>`',
                mention_author=False
            )
            return

        if not 0.0 <= threshold <= 1.0:
            await ctx.reply('Threshold must be between 0.0 and 1.0.', mention_author=False, delete_after=MSG_DEL_DELAY)
            return

        async with aiosqlite.connect(IMAGEMOD_DATABASE) as con:
            await con.execute(
                'INSERT INTO settings (KEY, VALUE) VALUES (?, ?) '
                'ON CONFLICT(KEY) DO UPDATE SET VALUE = excluded.VALUE',
                ('classification_threshold', str(threshold))
            )
            await con.commit()

        _manager.threshold = threshold

        embed = discord.Embed(
            title='Threshold Updated',
            description=f'Classification threshold set to **{threshold:.0%}**.',
            color=discord.Color.green()
        )
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False)

    # ─── Log channel command ────────────────────────────────────────────

    @commands.command(name='setlogchannel', aliases=['slc', 'logchannel'])
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
