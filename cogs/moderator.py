from datetime import datetime, timezone

import aiosqlite
import discord
from discord.ext import commands

from cogs.utils.constants import (BOTVERSION, COMMAND_PREFIX, MSG_DEL_DELAY,
                                  PERMISSIONS_DATABASE)


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
        - imagescreen
        '''
        embed = discord.Embed(title='Commands Module', description=f'To see how to use the Commands module use:\n`{COMMAND_PREFIX}help commands`\n\n\
            Current modules:\n- chatai\n- economy\n- imagescreen\n\n', color=0x00ff00, timestamp=datetime.now(timezone.utc))
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

    @commands_base.command(name='imagescreen', description='Enable or disable image screening in the channel.')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def commands_imagescreen(self, ctx, action: str):
        '''
        Enable or disable image screening for the current channel.
        When enabled, images posted in this channel will be automatically
        analysed by a local AI model and flagged if inappropriate.
        Use the following format for the command:
        `commands imagescreen <'enable' or 'disable'>`
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
            async with con.execute('INSERT OR REPLACE INTO imagescreen (server_id, channel_id, enabled) VALUES (?, ?, ?)', (guild_id, channel_id, channel_permission)) as cursor:
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
            async with con.execute('SELECT enabled, channel_id FROM imagescreen WHERE server_id = ?', (guild_id, )) as cursor:
                imagescreen_channels = await cursor.fetchall()

        imagescreen_list = []
        if imagescreen_channels:
            for enabled, channel_id in imagescreen_channels:
                if enabled:
                    channel = ctx.guild.get_channel(channel_id)
                    if channel:
                        imagescreen_list.append(f"#{channel.name}")
            if imagescreen_list:
                embed.add_field(name='Image Screening Enabled Channels', value='\n'.join(imagescreen_list) or "None", inline=False)
            else:
                embed.add_field(name='Image Screening Enabled Channels', value="None", inline=False)
        else:
            embed.add_field(name='Image Screening Enabled Channels', value="None", inline=False)

        await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        '''
        Kicks a member from the server.
        '''
        ...
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        '''
        Purges a specified amount of messages.
        '''
        ...
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        '''
        Bans a member from the server.
        '''
        ...
    

async def setup(bot):
    await bot.add_cog(ModCommands(bot))