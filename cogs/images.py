import os
import discord
from PIL import Image
from io import BytesIO
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
from discord.ext import commands

imagepath = os.path.abspath(os.getcwd())+'/images/'


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Images module online')

    @commands.command(name='speech')
    async def add_speech_bubble(self, ctx, user: discord.Member = None, *, message):
        speech_bubble = Image.open(imagepath+'speech_bubble.png')
        pass
        
        

def setup(bot):
    bot.add_cog(Images(bot))