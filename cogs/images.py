import glob
import os
import random
import discord
import textwrap
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
from discord.ext import commands
from io import BytesIO
from discord import File

imagepath = os.path.abspath(os.getcwd())+'/images/'


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Images module online')
    
    '''
    #!react to a message with a random react image with a speech bubble above and their message above that
    speech_bubble   underside of a speech bubble
    reaction0       anime
    reaction1       wutface
    reaction2       reallynigga face
    reaction3       disapair face
    reaction4       glowing agent
    
    '''
    @commands.command(name='react')
    async def add_speech_bubble(self, ctx, user: discord.Member = None, *, message):
        if ctx.reference:
            total_images = glob.glob(imagepath+'*.png')
            i = random.randint(0, len(total_images))
            reac_img = Image.open(imagepath+f'reaction{i}.png')
            speech_bubble = Image.open(imagepath+'speech_bubble.png')
            font = ImageFont.truetype(imagepath+'impact.ttf', 50)
            
            reac_width, reac_height = reac_img.size
            sb_width, sb_height = speech_bubble.size
            img_text_height = 200
            speech_bubble = speech_bubble.resize((reac_width, sb_height))
        
            reacted_to_user = ctx.reference.resolved.author.name 
            reacted_to_message = ctx.reference.resolved.content
            text_for_img = f'{reacted_to_user}: {reacted_to_message}'
            text_img = Image.new('RGB', (reac_width, 200), (255, 255, 255))
            draw = ImageDraw.Draw(text_img)
            draw.text((reac_width/2, img_text_height/2), text_for_img, font=font)
            
            final_img = Image.new('RGB', (reac_width, img_text_height+sb_height+reac_height))
            final_img.paste(text_img, (0, 0))
            final_img.paste(speech_bubble, (0, img_text_height))
            final_img.paste(reac_img, (0, img_text_height+sb_height))
            final_img.save(imagepath+'final_react.png', 'PNG')
            
            with open(imagepath+'final_react.png', 'rb') as f:
                img = File(f)
                await ctx.channel.send(file=img)
        else:
            await ctx.channel.reply(f"You didn't react to anything bozo, I haven't made that part of the command yet")


def setup(bot):
    bot.add_cog(Images(bot))