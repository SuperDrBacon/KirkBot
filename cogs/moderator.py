from datetime import datetime, timezone

import aiosqlite
import discord
from datetime import datetime, timezone
from discord.ext import commands

from cogs.utils.constants import (BOTVERSION, COMMAND_PREFIX, MSG_DEL_DELAY,
                                  OWNER_ID, PERMISSIONS_DATABASE)


class ModCommands(commands.Cog):
    '''
    This module houses all the moderation commands.
    '''
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
            print('moderator module online')
    
    @commands.group(name='commands', aliases=["cmd", "cmds"], description='Enable or disable commands in the current channel.', invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def commands_base(self, ctx):
        '''
        Enable or disable commands for the current channel.
        Select which module you want to enable or disable.
        Use the following format for the command:
        `commands <module> <'enable' or 'disable'>`
        
        Current modules:
        - chatai
        - economy
        - imagemod
        '''
        embed = discord.Embed(title='Commands Module', description=f'To see how to use the Commands module use:\n`{COMMAND_PREFIX}help commands`\n\n\
            Current modules:\n- chatai\n- economy\n- imagemod\n\n', color=0x00ff00, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)

    @commands_base.command(name='chatai', description='Enable or disable the chatbot AI in the channel.')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def commands_chatai(self, ctx, action: str):
        '''
        Enable or disable the chatbot AI for the current channel.
        Use the following format for the command:
        `commands chatai <'enable' or 'disable'>`
        '''
        action = action.lower()
        if action not in ["enable", "disable"]:
            await ctx.reply("Invalid action. Use 'enable' or 'disable'.", mention_author=False, delete_after=MSG_DEL_DELAY)
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            return
        
        channel_permission = (action == "enable")
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('INSERT OR REPLACE INTO chatai (server_id, channel_id, enabled) VALUES (?, ?, ?)', (guild_id, channel_id, channel_permission)) as cursor:
                await con.commit()
        
        await ctx.reply(f'Chat AI module {action}d for this channel.', mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)

    @commands_base.command(name='economy', description='Enable or disable economy commands in the channel.')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def commands_economy(self, ctx, action: str):
        '''
        Enable or disable economy commands for the current channel.
        Use the following format for the command:
        `commands economy <'enable' or 'disable'>`
        '''
        action = action.lower()
        if action not in ["enable", "disable"]:
            await ctx.reply("Invalid action. Use 'enable' or 'disable'.", mention_author=False, delete_after=MSG_DEL_DELAY)
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            return
        
        channel_permission = (action == "enable")
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('INSERT OR REPLACE INTO economy (server_id, channel_id, enabled) VALUES (?, ?, ?)', (guild_id, channel_id, channel_permission)) as cursor:
                await con.commit()
        #                            enable/disable
        await ctx.reply(f'Economy commands {action}d for this channel.', mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)

    @commands_base.command(name='imagemod', description='Enable or disable image screening in the channel.')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def commands_imagemod(self, ctx, action: str):
        '''
        Enable or disable image screening for the current channel.
        When enabled, images posted in this channel will be automatically
        analysed by a local AI model and flagged if inappropriate.
        Use the following format for the command:
        `commands imagemod <'enable' or 'disable'>`
        '''
        action = action.lower()
        if action not in ["enable", "disable"]:
            await ctx.reply("Invalid action. Use 'enable' or 'disable'.", mention_author=False, delete_after=MSG_DEL_DELAY)
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            return

        channel_permission = (action == "enable")
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('INSERT OR REPLACE INTO imagemod (server_id, channel_id, enabled) VALUES (?, ?, ?)', (guild_id, channel_id, channel_permission)) as cursor:
                await con.commit()

        await ctx.reply(f'Image screening {action}d for this channel.', mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)

    @commands_base.command(name='show', description='Show the current command settings for this server.')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def commands_show(self, ctx):
        '''
        Show which commands are enabled in which channels for this server.
        '''
        guild_id = ctx.guild.id
        embed = discord.Embed(title="Command Settings", color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=BOTVERSION)
        
        # Get ChatAI permissions
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('SELECT enabled, channel_id FROM chatai WHERE server_id = ?', (guild_id, )) as cursor:
                chatai_channels = await cursor.fetchall()
        
        # Get Economy permissions
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('SELECT enabled, channel_id FROM economy WHERE server_id = ?', (guild_id, )) as cursor:
                economy_channels = await cursor.fetchall()
        
        # Add ChatAI enabled channels to embed
        chatai_list = []
        if chatai_channels:
            for enabled, channel_id in chatai_channels:
                if enabled:
                    channel = ctx.guild.get_channel(channel_id)
                    if channel:
                        chatai_list.append(f"#{channel.name}")
            if chatai_list:
                embed.add_field(name='ChatAI Enabled Channels', value='\n'.join(chatai_list) or "None", inline=False)
            else:
                embed.add_field(name='ChatAI Enabled Channels', value="None", inline=False)
        else:
            embed.add_field(name='ChatAI Enabled Channels', value="None", inline=False)
        
        # Add Economy enabled channels to embed
        economy_list = []
        if economy_channels:
            for enabled, channel_id in economy_channels:
                if enabled:
                    channel = ctx.guild.get_channel(channel_id)
                    if channel:
                        economy_list.append(f"#{channel.name}")
            if economy_list:
                embed.add_field(name='Economy Enabled Channels', value='\n'.join(economy_list) or "None", inline=False)
            else:
                embed.add_field(name='Economy Enabled Channels', value="None", inline=False)
        else:
            embed.add_field(name='Economy Enabled Channels', value="None", inline=False)

        # Get Image Screening permissions
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('SELECT enabled, channel_id FROM imagemod WHERE server_id = ?', (guild_id, )) as cursor:
                imagemod_channels = await cursor.fetchall()

        imagemod_list = []
        if imagemod_channels:
            for enabled, channel_id in imagemod_channels:
                if enabled:
                    channel = ctx.guild.get_channel(channel_id)
                    if channel:
                        imagemod_list.append(f"#{channel.name}")
            if imagemod_list:
                embed.add_field(name='Image Screening Enabled Channels', value='\n'.join(imagemod_list) or "None", inline=False)
            else:
                embed.add_field(name='Image Screening Enabled Channels', value="None", inline=False)
        else:
            embed.add_field(name='Image Screening Enabled Channels', value="None", inline=False)

        await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    # @commands.command()
    # @commands.has_permissions(kick_members=True)
    # async def kick(self, ctx, member: discord.Member, *, reason=None):
    #     '''
    #     Kicks a member from the server.
    #     '''
    #     ...
    
    # @commands.command()
    # @commands.has_permissions(manage_messages=True)
    # async def purge(self, ctx, amount: int):
    #     '''
    #     Purges a specified amount of messages.
    #     '''
    #     ...
    
    # @commands.command()
    # @commands.has_permissions(ban_members=True)
    # async def ban(self, ctx, member: discord.Member, *, reason=None):
    #     '''
    #     Bans a member from the server.
    #     '''
    #     ...
    
    @commands.command(name='initdb', hidden=True)
    async def init_permissions_table(self, ctx, table_name: str = None):
        r'''
        Create a new permissions table in the permissions database.
        Owner-only hidden command. Creates the standard (server_id, channel_id, enabled) schema.
        Usage: `initdb <table_name>` or `initdb` to list existing tables.
        '''
        if ctx.author.id != OWNER_ID:
            return

        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            # No argument — show existing tables
            if table_name is None:
                async with con.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
                    tables = [row[0] for row in await cursor.fetchall()]
                await ctx.reply(f"**Existing permissions tables:**\n`{'`, `'.join(tables)}`", mention_author=False)
                return

            # Sanitise: only allow simple alphanumeric/underscore names
            if not table_name.replace('_', '').isalnum():
                await ctx.reply("Invalid table name. Use only letters, numbers, and underscores.", mention_author=False, delete_after=MSG_DEL_DELAY)
                return

            # Create the table
            await con.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    SERVER_ID   INTEGER NOT NULL,
                    CHANNEL_ID  INTEGER NOT NULL,
                    ENABLED     BOOLEAN NOT NULL DEFAULT FALSE,
                    PRIMARY KEY (SERVER_ID, CHANNEL_ID))
            ''')
            await con.commit()

        await ctx.reply(f"✅ Permissions table `{table_name}` created (or already exists).", mention_author=False)

async def setup(bot):
    await bot.add_cog(ModCommands(bot))