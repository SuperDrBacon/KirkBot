import random
import discord
import asyncio
from pypresence import Presence
from discord.ext import commands


class Presence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Presence module online')
    
    async def change_presence(self):
        print('Waiting to start change_presence')
        await self.bot.wait_until_ready()
        print('change_presence started')
        
        statuses = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        while not self.bot.is_closed():
            status = random.choice(statuses)
            await self.bot.change_presence(activity=discord.Game(name=status))
            await asyncio.sleep(10)

def setup(bot):
    bot.add_cog(Presence(bot))
