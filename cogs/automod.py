import discord
from discord.ext import commands


class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Automod module online')

    @commands.Cog.listener()
    async def on_message(self, ctx): 
        pass

        # message = ctx.content
        # if message == "":
        #     message = ctx.attachments[0].url
        
        




def setup(bot):
    bot.add_cog(Automod(bot))
