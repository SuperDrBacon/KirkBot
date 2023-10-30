import discord
from discord.ext import commands


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.Cog.listener()
    async def on_a(self, message):
        ...

async def setup(bot):
    await bot.add_cog(Log(bot))
