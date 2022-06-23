import asyncio
import glob
import os
import random
import discord
import textwrap
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
from configparser import ConfigParser
from discord.ext import commands
from io import BytesIO
from discord import File

path = os.path.abspath(os.getcwd())
imagepath = rf'{path}/images/'

config = ConfigParser()
config.read(rf'{path}/config.ini')

prefix = config['BOTCONFIG']['prefix']

class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Images module online')
    
    '''
    React to a message with a random react image with a speech bubble above and their message above that
    '''
    @commands.command(name='react')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def add_speech_bubble(self, ctx, *, facetype:str = ''):
        react_images = []            
        for filename in os.listdir(os.path.abspath(os.getcwd()) + "/images"):
            if filename.startswith('react'):
                react_images.append(filename[6:-4])
        choices = ''
        for choice in react_images:
            choices += ''.join(f'{choice}, ')
                
        if facetype.lower() in react_images:
            reac_img = Image.open(f'{imagepath}react {facetype}.png')
        else:
            randomfacetype = random.choice(react_images)
            reac_img = Image.open(f'{imagepath}react {randomfacetype}.png')
            if ctx.message.reference:
                msg = await ctx.reply(f'Didn\'t specify a reaction type, picking random one for now: **{randomfacetype} face**. Available choices are: **{choices}**')
            
            
        if ctx.message.reference:   
            speech_bubble = Image.open(imagepath+'speech_bubble.png')
            font = ImageFont.truetype(imagepath+'impact.ttf', 30)
            
            img_width = 500
            reac_width, reac_height = reac_img.size

            new_scale = 1 + ((img_width-reac_width)/reac_width)
            sb_width, sb_height = speech_bubble.size

            new_reac_height = round(reac_height * new_scale)
            speech_bubble = speech_bubble.resize((img_width, sb_height))
            reac_img = reac_img.resize((img_width, new_reac_height))
            
            reacted_to_user = ctx.message.reference.resolved.author.name 
            reacted_to_message = ctx.message.reference.resolved.content
            text_for_img = f'{reacted_to_user}: {reacted_to_message}'
            fontw, fonth = font.getsize(text_for_img)
            lines = textwrap.wrap(text_for_img, width=40)
            
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
            mgs2 = await ctx.reply(f"React to a message to use this command. Specify an image by using these keywords: **{choices}** use {prefix}caption to caption last image in chat.")
        
        await asyncio.sleep(10)
        
        if ctx.message.reference and facetype.lower() not in react_images:  
            await msg.delete()
        
        if not ctx.message.reference:
            await mgs2.delete()
            await ctx.message.delete()
    
    # '''
    # Caption the previous image or gif posted in the chat
    # '''
    # @commands.command(name='caption')
    # @commands.cooldown(1, 5, commands.BucketType.user)
    # async def caption_image(self, ctx):
    #     messages = await ctx.channel.history(limit=50, oldest_first=False).flatten()
    #     print('01')
    #     for message in messages:
    #         print('11')
    #         if message.attachments:
    #             print('101')
    #             print(message.attachments)
    #             for attachment in message.attachments:
    #                 if attachment.filename.endswith('.png') or attachment.filename.endswith('.jpg') or attachment.filename.endswith('.gif'):
    #                     try:
    #                         # img = Image.open(attachment.url)
    #                         print('1')
    #                         await attachment.save(imagepath+'dl temp.png', use_cashed=False)
    #                     except:
    #                         try:
    #                             print('2')
    #                             # img = Image.open(attachment.proxy_url)
    #                             attachment.save(imagepath+'dl temp.png', use_cashed=True)
    #                         except:
    #                             return await ctx.reply('Failed to download image')
    #                         # font = ImageFont.truetype(imagepath+'impact.ttf', 30)
    #                         # img_width = 500
    #                         # img_height = img.size[1]




def setup(bot):
    bot.add_cog(Images(bot))