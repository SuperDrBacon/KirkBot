import random
import discord
import asyncio
import os
from discord.ext import commands, tasks
from configparser import ConfigParser
from pypresence import Presence 


ospath = os.path.abspath(os.getcwd())
info = ConfigParser()
config = ConfigParser()
info.read(rf'{ospath}/info.ini')
config.read(rf'{ospath}/config.ini')

command_prefix = config['BOTCONFIG']['prefix']
status = info['STATUS']['status']
activity = discord.Activity(name=status, type=discord.ActivityType.watching)
started_tasks = []

SECOND_LOOP_DELAY = 10

class StatusManager(commands.Cog):
    '''
    Manages the bot's status.
    '''
    def __init__(self, bot):
        self.bot = bot
        self.switch_status_task = None
        if not self.switch_status_task or self.switch_status_task.done():
            self.switch_status_task = asyncio.create_task(self.switch_status_loop())
    
    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Status module online')
    
    #commands
    @commands.group(name='botstatus', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def botstatus_base(self, ctx):
        '''
        This command group is used to change the bot's status.
        It Gets the current status of the bot and send it as a message to the channel.
        '''
        await ctx.channel.send(f'current status is: {status}')
    
    @botstatus_base.command(name='set')
    @commands.has_permissions(administrator=True)
    async def setbotstatus(self, ctx, *, statusmessage):
        '''
        Changes the bot's status message to the given `statusmessage`.
        Prompts the user to select whether the bot should be "watching" or "listening to" the status message.
        Updates the bot's status and saves the new status message to the `info.ini` file.
        '''
        message = await ctx.send(f"[1️⃣ for watching]. [2️⃣ for listening to.]")
        await message.add_reaction('1️⃣')
        await message.add_reaction('2️⃣')
        
        check = lambda r, u: u == ctx.author and str(r.emoji) in "1️⃣2️⃣"
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=10)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            await ctx.message.delete()
            await message.edit(content="update cancelled, timed out.")
            return
        
        if str(reaction.emoji) == "1️⃣":
            activity = discord.Activity(name=statusmessage, type=discord.ActivityType.watching)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            strstatus = 'Watching'
        
        elif str(reaction.emoji) == "2️⃣":
            activity = discord.Activity(name=statusmessage, type=discord.ActivityType.listening)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            strstatus = 'Listening to'
        
        else:
            await message.edit(content="Update cancelled.")
            return
        
        info.set('STATUS', 'status', statusmessage)
        
        with open(rf'{ospath}/info.ini', 'w') as infofile:
            info.write(infofile)
        await message.edit(content=f'Updated Status to: {strstatus} {statusmessage}')
        await message.clear_reactions()
    
    async def cog_unload(self):
        # print('Autodelete cog_unload stopping switch_status_loop')
        if self.switch_status_task and not self.switch_status_task.done():
            self.switch_status_task.cancel()
    
    async def cog_load(self):
        await asyncio.sleep(2)
        # print('Autodelete cog_load starting switch_status_loop')
        if self.switch_status_task and self.switch_status_task.done():
            loop = asyncio.get_event_loop()
            self.switch_status_task = loop.create_task(self.switch_status_loop())
            await self.fetch_missed_messages()
    
    @commands.Cog.listener()
    async def on_disconnect(self):
        if self.switch_status_task and not self.switch_status_task.done():
            self.switch_status_task.cancel()
    
    @commands.Cog.listener()
    async def on_resumed(self):
        await asyncio.sleep(2)
        if self.switch_status_task and self.switch_status_task.done():
            loop = asyncio.get_event_loop()
            self.switch_status_task = loop.create_task(self.switch_status_loop())
            await self.fetch_missed_messages()
    
    async def switch_status_loop(self):
        while True:
            # print ('switch_status_loop')
            activity = discord.Activity(name=status, type=discord.ActivityType.watching)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            await asyncio.sleep(SECOND_LOOP_DELAY)
            
            activity = discord.Activity(name=f'{command_prefix}help', type=discord.ActivityType.playing)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            await asyncio.sleep(SECOND_LOOP_DELAY)
    
async def setup(bot):
    await bot.add_cog(StatusManager(bot))