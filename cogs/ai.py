import discord
import openai
import os
from discord.ext import commands
from configparser import ConfigParser

config = ConfigParser()
configpath = os.path.abspath(os.getcwd())
configini = '/'.join([configpath, "config.ini"])
config.read(configini)

key = config['BOTCONFIG']['openaiAPI']


class Ai(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('logger module online')

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot:
            return
        # pass
        if ctx.content.startswith('<@!937050268007268452>' or '<@937050268007268452>'):
            print('reaction ti newaase')
            







def setup(bot):
    bot.add_cog(Ai(bot))
