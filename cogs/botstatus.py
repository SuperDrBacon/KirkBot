import discord
import asyncio
import os
import traceback
from discord.ext import commands
from configparser import ConfigParser


config = ConfigParser()
configpath = os.path.abspath(os.getcwd())
configini = '/'.join([configpath, "config.ini"])
config.read(configini)

status = config['STATUS']['status']
activity = discord.Activity(name=status, type=discord.ActivityType.watching)

class setStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print('status module online')
        return await self.bot.change_presence(status=discord.Status.online, activity=activity)

    #commands
    @commands.group(name='botstatus', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def botstatus_base(self, ctx):
        await ctx.channel.send(f'current status is: {status}')

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

        # await ctx.message.delete()
        config.set('STATUS', 'status', statusmessage)
        # config.write(configpath.open('w'))
        with open(configini, 'w') as configfile:
            config.write(configfile)
        await message.edit(content=f'Updated Status to: {strstatus} {statusmessage}')
        await message.clear_reactions()

def setup(bot):
    bot.add_cog(setStatus(bot))
