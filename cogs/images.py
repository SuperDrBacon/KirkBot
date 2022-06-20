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
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def add_speech_bubble(self, ctx):
        if ctx.message.reference:
            
            total_images = glob.glob(imagepath+'reaction*')
            
            i = random.randint(0, len(total_images-1))
            # print(f'{i} of total {len(total_images)}')
            reac_img = Image.open(imagepath+f'reaction{i}.png')
            speech_bubble = Image.open(imagepath+'speech_bubble.png')
            font = ImageFont.truetype(imagepath+'impact.ttf', 30)
            
            img_width = 500
            reac_width, reac_height = reac_img.size
            print(reac_width)
            new_scale = 1 + ((img_width-reac_width)/reac_width)
            sb_width, sb_height = speech_bubble.size
            # img_text_height = 200
            print(new_scale)
            new_reac_height = round(reac_height * new_scale)
            speech_bubble = speech_bubble.resize((img_width, sb_height))
            reac_img = reac_img.resize((img_width, new_reac_height))
            
            reacted_to_user = ctx.message.reference.resolved.author.name 
            reacted_to_message = ctx.message.reference.resolved.content
            text_for_img = f'{reacted_to_user}: {reacted_to_message}'
            fontw, fonth = font.getsize(text_for_img)
            lines = textwrap.wrap(text_for_img, width=40)
            # print(lines)
            y_offset = (len(lines)*fonth)/2
            img_text_height = fonth * len(lines) + 50
            y_text = (img_text_height/2)-(fonth/2) - y_offset
            text_img = Image.new('RGB', (img_width, img_text_height), (255, 255, 255))
            for line in lines:
                linew, lineh = font.getsize(line)
                draw = ImageDraw.Draw(text_img)
                draw.text(((img_width/2)-(linew/2), y_text), line, (0, 0, 0), font=font)
                y_text += lineh
            
            final_img = Image.new('RGB', (img_width, img_text_height+sb_height+new_reac_height))
            final_img.paste(text_img, (0, 0))
            final_img.paste(speech_bubble, (0, img_text_height))
            final_img.paste(reac_img, (0, img_text_height+sb_height))
            final_img.save(imagepath+'final_react.png', 'PNG')
            
            await ctx.reply(file=discord.File(imagepath+'final_react.png'))
            
        else:
            await ctx.reply(f"You didn't react to anything bozo, I haven't made that part of the command yet")


def setup(bot):
    bot.add_cog(Images(bot))