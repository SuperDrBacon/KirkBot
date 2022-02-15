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
openai.api_key = key

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
        if ctx.content.startswith('<@!937050268007268452>') or ctx.content.startswith('<@937050268007268452>'):
            message = ctx.content + '.'
            response = openai.Completion.create(
                engine="text-davinci-001",
                prompt=message,
                temperature=0.9,
                max_tokens=500,
                n=1,
                frequency_penalty=0.2,
                presence_penalty=0.2,
                stop=["."]
            )
            out = response.choices[0].text
            await ctx.reply(out)







def setup(bot):
    bot.add_cog(Ai(bot))
