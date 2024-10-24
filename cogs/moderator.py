import os
import aiosqlite
import discord
import asyncio
from datetime import datetime, timezone
from discord.ext import commands
from discord.ext.commands import CheckFailure
from configparser import ConfigParser

import cogs.utils.functions as functions

ospath = os.path.abspath(os.getcwd())
config, info = ConfigParser(), ConfigParser()
info.read(rf'{ospath}/info.ini')
config.read(rf'{ospath}/config.ini')
command_prefix = config['BOTCONFIG']['prefix']
botversion = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']
permissions_database = rf'{ospath}/cogs/permissions_data.db'

MSG_DEL_DELAY = 10

class ModCommands(commands.Cog):
    '''
    This module houses all the moderation commands.
    '''
    def __init__(self, bot):
        self.bot = bot
        functions.checkForFile(filepath=os.path.dirname(permissions_database), filename=os.path.basename(permissions_database), database=True, dbtype='permissions')

    @commands.Cog.listener()
    async def on_ready(self):
            print('moderator module online')
    
    @commands.group(name='setpermissions', aliases=["setperm", "setperms"], description='Set the permissions for the current channel.', invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def set_permissions_base(self, ctx):
        '''
        Set the permissions for the current channel.
        Select which module you want to enable or disable.
        Use the following format for the command:
        `setpermissions <module> <'True' or 'False'>`
        
        Current modules:
            - chatai
        '''
        embed = discord.Embed(title='Set Permissions usage', description=f'To see how to use the Set Permissions module use:\n`{command_prefix}help setpermissions`\n\n\
            Current modules:\n\t- chatai\n\n', color=0x00ff00, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=botversion)
        await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @set_permissions_base.command(name='chatai', description='Enable or disable the chatbot AI in the channel.')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def set_chatai_permissions(self, ctx, channel_permission:bool):
        '''
        Set the permissions for the current channel.
        Select which module you want to enable or disable.
        Use the following format for the command:
        `setpermissions <module> <'True' or 'False'>`
        '''
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        async with aiosqlite.connect(permissions_database) as con:
            async with con.execute('INSERT OR REPLACE INTO chatai (server_id, channel_id, enabled) VALUES (?, ?, ?)', (guild_id, channel_id, channel_permission)) as cursor:
                await con.commit()
        await ctx.reply(f'Chat AI module {"enabled" if channel_permission else "disabled"} for this channel.', mention_author=False, delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @set_permissions_base.command(name='show', description='Show the current permissions for the chatbot AI in the channel.')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def show_permissions(self, ctx):
        '''
        Show the current permissions for the chatbot AI in the channel.
        '''
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        async with aiosqlite.connect(permissions_database) as con:
            async with con.execute('SELECT enabled FROM chatai WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)) as cursor:
                enabled = (result := await cursor.fetchone()) is not None and result[0]
        await ctx.reply(f'Chat AI module is {"enabled" if enabled else "disabled"} for this channel.', mention_author=False, delete_after=MSG_DEL_DELAY)
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