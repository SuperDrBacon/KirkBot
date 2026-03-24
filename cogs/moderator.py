from datetime import datetime, timezone

import aiosqlite
import discord
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
        - invitelog
        '''
        embed = discord.Embed(title='Commands Module', description=f'To see how to use the Commands module use:\n`{COMMAND_PREFIX}help commands`\n\n\
            Current modules:\n- chatai\n- economy\n- imagemod\n- invitelog\n\n', color=0x00ff00, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)

    @commands_base.command(name='chatai', description='Enable or disable the chatbot AI in the channel.')
    @commands.has_permissions(administrator=True)
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
    @commands.has_permissions(administrator=True)
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

    @commands_base.command(name='imagemod', description='Enable or disable image screening.')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def commands_imagemod(self, ctx, action: str):
        '''
        Enable or disable image screening for this server.
        When enabled, images posted in this server will be automatically
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

        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('INSERT OR REPLACE INTO imagemod (server_id, enabled) VALUES (?, ?)', (guild_id, channel_permission)) as cursor:
                await con.commit()

        await ctx.reply(f'Image screening {action}d.', mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)

    @commands_base.command(name='invitelog', description='Set or disable the invite log channel for this server.')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def commands_invitelog(self, ctx, action: str):
        '''
        Set or disable the invite log channel for this server.
        When enabled, member join events will be logged to the current channel.
        Use the following format for the command:
        `commands invitelog <'enable' or 'disable'>`
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
            async with con.execute('INSERT OR REPLACE INTO invitelog (server_id, channel_id, enabled) VALUES (?, ?, ?)', (guild_id, channel_id, channel_permission)) as cursor:
                await con.commit()

        if channel_permission:
            await ctx.reply(f'Invite log enabled. Join events will be sent to {ctx.channel.mention}.', mention_author=False, delete_after=MSG_DEL_DELAY)
        else:
            await ctx.reply('Invite log disabled for this server.', mention_author=False, delete_after=MSG_DEL_DELAY)
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

        # Get Image Screening status (server-wide, not per-channel)
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('SELECT enabled FROM imagemod WHERE server_id = ?', (guild_id,)) as cursor:
                imagemod_row = await cursor.fetchone()

        if imagemod_row and imagemod_row[0]:
            embed.add_field(name='Image Screening', value='✅ Enabled', inline=False)
        else:
            embed.add_field(name='Image Screening', value='❌ Disabled', inline=False)

        # Get InviteLog channel
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('SELECT enabled, channel_id FROM invitelog WHERE server_id = ?', (guild_id,)) as cursor:
                invitelog_row = await cursor.fetchone()

        if invitelog_row and invitelog_row[0]:
            channel = ctx.guild.get_channel(invitelog_row[1])
            channel_name = f"#{channel.name}" if channel else "Unknown channel"
            embed.add_field(name='Invite Log Channel', value=f'✅ {channel_name}', inline=False)
        else:
            embed.add_field(name='Invite Log Channel', value='❌ Disabled', inline=False)

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
        Owner-only hidden command. Creates the standard (server_id, enabled) schema.
        Usage: `initdb <table_name>` or `initdb` to list existing tables.
        '''
        if ctx.author.id != OWNER_ID:
            await ctx.reply('Only the bot owner can use this command.', mention_author=False, delete_after=MSG_DEL_DELAY)
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

            # Create the table — invitelog needs an extra channel_id column
            if table_name == 'invitelog':
                await con.execute('''
                    CREATE TABLE IF NOT EXISTS invitelog (
                        server_id   INTEGER NOT NULL PRIMARY KEY,
                        channel_id  INTEGER,
                        enabled     BOOLEAN NOT NULL DEFAULT FALSE)
                ''')
                # Add channel_id if the table already existed without it
                async with con.execute('PRAGMA table_info(invitelog)') as cursor:
                    columns = [row[1] for row in await cursor.fetchall()]
                if 'channel_id' not in columns:
                    await con.execute('ALTER TABLE invitelog ADD COLUMN channel_id INTEGER')
            else:
                await con.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        SERVER_ID   INTEGER NOT NULL PRIMARY KEY,
                        ENABLED     BOOLEAN NOT NULL DEFAULT FALSE)
                ''')
            await con.commit()

        await ctx.reply(f"✅ Permissions table `{table_name}` created (or already exists).", mention_author=False)

async def setup(bot):
    await bot.add_cog(ModCommands(bot))