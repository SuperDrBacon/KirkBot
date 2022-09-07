import random
import discord
import asyncio
import os
import traceback
import time
from discord.ext import commands, tasks
from configparser import ConfigParser
from pypresence import Presence 


path = os.path.abspath(os.getcwd())
info = ConfigParser()
info.read(rf'{path}/info.ini')

status = info['STATUS']['status']
activity = discord.Activity(name=status, type=discord.ActivityType.watching)

class setStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Status module online')
        await self.bot.change_presence(status=status, activity=activity)

    #commands
    @commands.has_permissions(administrator=True)
    @commands.group(name='botstatus', invoke_without_command=True)
    async def botstatus_base(self, ctx):
        await ctx.channel.send(f'current status is: {status}')
    
    @commands.has_permissions(administrator=True)
    @botstatus_base.command(name='set', invoke_without_command=False)
    async def setbotstatus(self, ctx, *, statusmessage):
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

        with open(rf'{path}/info.ini', 'w') as infofile:
            info.write(infofile)
        await message.edit(content=f'Updated Status to: {strstatus} {statusmessage}')
        await message.clear_reactions()

async def setup(bot):
    await bot.add_cog(setStatus(bot))

async def change_presence(self):
    print('Waiting to start change_presence')
    await self.bot.wait_until_ready()
    print('change_presence started')

    statuses = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
    while not self.bot.is_closed():
        status = random.choice(statuses)
        await self.bot.change_presence(activity=discord.Game(name=status))
        await asyncio.sleep(10)