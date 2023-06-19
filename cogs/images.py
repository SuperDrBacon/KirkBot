import asyncio
import os
import random
import shutil
import discord
import textwrap
import requests
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageSequence
from PIL import ImageOps
from configparser import ConfigParser
from discord.ext import commands
from io import BytesIO
from string import ascii_letters
from bs4 import BeautifulSoup

ua = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'}

path = os.path.abspath(os.getcwd())
imagepath = rf'{path}/images/'

config = ConfigParser()
config.read(rf'{path}/config.ini')

prefix = config['BOTCONFIG']['prefix']

class Images(commands.Cog):
    '''
    This module contains commands that use and create images.
    '''
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Images module online')
    
    @commands.command(name='react')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def add_speech_bubble(self, ctx, *, facetype:str = ''):
        '''
        React to a message with a random react image with a speech bubble above and their message above that.
        '''
        byteio = BytesIO()
        react_images = []            
        print(imagepath)
        for filename in os.listdir(imagepath):
            if filename.startswith('react'):
                react_images.append(filename[6:-4])
        choices = ''
        for choice in react_images:
            choices += ''.join(f"{choice}{'.' if choice == react_images[-1] else ','}")
        
        if facetype.lower() in react_images:
            reac_img = Image.open(f'{imagepath}react {facetype}.png')
        else:
            randomfacetype = random.choice(react_images)
            reac_img = Image.open(f'{imagepath}react {randomfacetype}.png')
            if ctx.message.reference:
                msg = await ctx.reply(f'Didn\'t specify a reaction type, picking random one for now: **{randomfacetype} face**. Available choices are: **{choices}**')
        
        if ctx.message.reference:   
            speech_bubble = Image.open(imagepath+'speech_bubble.png')
            font = ImageFont.truetype(imagepath+'impact.ttf', 60)
            
            img_width = 1000
            reac_width, reac_height = reac_img.size
            sb_height = speech_bubble.size[1]
            fonth = font.getsize(text_for_img)[1]
            new_scale = 1 + ((img_width-reac_width)/reac_width)
            new_reac_height = round(reac_height * new_scale)
            
            speech_bubble = speech_bubble.resize((img_width, sb_height))
            reac_img = reac_img.resize((img_width, new_reac_height))
            
            reacted_to_user = ctx.message.reference.resolved.author.name 
            reacted_to_message = ctx.message.reference.resolved.content
            text_for_img = f'{reacted_to_user}: {reacted_to_message}'
            
            avg_char_width = sum(font.getsize(char)[0] for char in ascii_letters) / len(ascii_letters)
            max_char_count = int((img_width * 0.95) / avg_char_width)
            lines = textwrap.wrap(text_for_img, width=max_char_count)
            
            padding = 80
            text_img_height = fonth * len(lines) + padding
            text_y_start = (0.5 * padding) + (0.5 * fonth)
            
            text_img = Image.new('RGBA', (img_width, text_img_height), (255, 255, 255, 255))
            for line in lines:
                linew = font.getsize(line)[0]
                draw = ImageDraw.Draw(text_img)
                draw.text(((img_width/2)-(linew/2), text_y_start-(fonth/2)), line, (0, 0, 0, 255), font=font)
                text_y_start += fonth
            
            final_img = Image.new('RGBA', (img_width, text_img_height+sb_height+new_reac_height), (0, 0, 0, 0))
            final_img.paste(text_img, (0, 0))
            final_img.paste(speech_bubble, (0, text_img_height))
            final_img.paste(reac_img, (0, text_img_height+sb_height))
            final_img.save(byteio, format='PNG')
            byteio.seek(0)
            
            await ctx.reply(file=discord.File(byteio, filename='Final_react.png'))            
        else:
            mgs2 = await ctx.reply(f"React to a message to use this command. Specify an image by using these keywords: **{choices}** Use {prefix}help to see other image commands.")
        
        await asyncio.sleep(10)
        
        if ctx.message.reference and facetype.lower() not in react_images:  
            await msg.delete()
        
        if not ctx.message.reference:
            await mgs2.delete()
            await ctx.message.delete()
    
    @commands.command(name='caption')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def caption_image(self, ctx, *, caption:str = ''):
        '''
        Caption the previous image or gif posted in the chat.
        '''
        byteio = BytesIO()
        messages = await ctx.channel.history(limit=50, oldest_first=False).flatten()
        if os.path.exists(imagepath+'dl temp.png'):
            os.remove(imagepath+'dl temp.png')
        if os.path.exists(imagepath+'dl temp.gif'):
            os.remove(imagepath+'dl temp.gif')
        try:
            for message in messages:
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.filename.endswith('.png') or attachment.filename.endswith('.jpg'):
                            try:
                                await attachment.save(byteio, format='PNG', use_cached=False)                     
                            except Exception as e:
                                try:
                                    await attachment.save(byteio, format='PNG', use_cached=True)
                                except Exception as ee:
                                    print(f'{e} -EN- {ee}')
                                    return await ctx.reply('Failed to get image png jpg')
                            raise StopIteration
                        elif attachment.filename.endswith('.gif'):
                            try:
                                await attachment.save(imagepath+'dl temp.gif', use_cached=False)
                            except Exception as e:
                                try:
                                    await attachment.save(imagepath+'dl temp.gif', use_cached=True)
                                except Exception as ee:
                                    print(f'{e} -EN- {ee}')
                                    return await ctx.reply('Failed to get image gif')
                            raise StopIteration
                elif message.content.endswith('.gif'):
                    try:
                        response = requests.get(message.content, stream=True)
                        with open(imagepath+'dl temp.gif', 'wb') as f:
                            response.raw.decode_content = True
                            shutil.copyfileobj(response.raw, f)
                    except Exception as e:
                        print(f'{e}')
                        return await ctx.reply('Failed to get image gif link.')
                    raise StopIteration
                #Ofcourse normal tenor links don't work	why would they?
                elif message.content.startswith('https://tenor.com/'):
                    try:
                        page = requests.get(message.content, headers=ua)
                        soup = BeautifulSoup(page.content, 'html.parser')
                        channels = soup.find('div', class_="Gif")
                        ctenor = channels.find('img').attrs['src']
                        response = requests.get(ctenor, stream=True)
                        with open(imagepath+'dl temp.gif', 'wb') as f:
                            response.raw.decode_content = True
                            shutil.copyfileobj(response.raw, f)
                    except Exception as e:
                        print(f'{e}')
                        return await ctx.reply('Failed to get image gif link.')
                    raise StopIteration
            return await ctx.reply('No image found in chat')
        except StopIteration:
            pass
        
        if os.path.exists(imagepath+'dl temp.png'):
            reac_img = Image.open(imagepath+'dl temp.png')
            reac_width, reac_height = reac_img.size
            if reac_width < 500:
                font = ImageFont.truetype(imagepath+'impact.ttf', 30)
            else:
                font = ImageFont.truetype(imagepath+'impact.ttf', 60)
            fontw, fonth = font.getsize(caption)
            
            avg_char_width = sum(font.getsize(char)[0] for char in ascii_letters) / len(ascii_letters)
            max_char_count = int((reac_width * 0.97) / avg_char_width)
            lines = textwrap.wrap(text=caption, width=max_char_count)
            
            y_offset = (len(lines)*fonth)/2
            img_text_height = fonth * len(lines) + 100
            y_text = (img_text_height/2)-(fonth/2) - y_offset
            text_img = Image.new('RGBA', (reac_width, img_text_height), (255, 255, 255))
            for line in lines:
                linew, lineh = font.getsize(line)
                draw = ImageDraw.Draw(text_img)
                draw.text(((reac_width/2)-(linew/2), y_text), line, (0, 0, 0), font=font)
                y_text += lineh
            
            final_img = Image.new('RGBA', (reac_width, img_text_height+reac_height))
            final_img.paste(text_img, (0, 0))
            final_img.paste(reac_img, (0, img_text_height))
            final_img.save(imagepath+'final_react.png', 'PNG')
            return await ctx.reply(file=discord.File(imagepath+'final_react.png')) 
        
        elif os.path.exists(imagepath+'dl temp.gif'):
            reac_gif = Image.open(imagepath+'dl temp.gif')
            font = ImageFont.truetype(imagepath+'impact.ttf', 60)
            reac_width, reac_height = reac_gif.size
            
            fontw, fonth = font.getsize(caption)
            
            avg_char_width = sum(font.getsize(char)[0] for char in ascii_letters) / len(ascii_letters)
            max_char_count = int((reac_width * 0.97) / avg_char_width)
            lines = textwrap.wrap(text=caption, width=max_char_count)
            
            y_offset = (len(lines)*fonth)/2
            img_text_height = fonth * len(lines) + 100
            y_text = (img_text_height/2)-(fonth/2) - y_offset
            text_img = Image.new('RGBA', (reac_width, img_text_height), (255, 255, 255))
            for line in lines:
                linew, lineh = font.getsize(line)
                draw = ImageDraw.Draw(text_img)
                draw.text(((reac_width/2)-(linew/2), y_text), line, (0, 0, 0), font=font)
                y_text += lineh
            
            quality = 100
            makegif(reac_gif, text_img, img_text_height, quality)
            
            try:
                await ctx.reply(file=discord.File(imagepath+'final_react.gif'))
            except Exception:
                try:
                    resizemsg = await ctx.reply(f'Hold on gif too big, resizing now.')
                    quality = 60
                    makegif(reac_gif, text_img, img_text_height, quality)
                    await ctx.reply(file=discord.File(imagepath+'final_react.gif'))
                except Exception:
                    try:
                        quality = 30
                        makegif(reac_gif, text_img, img_text_height, quality)
                        await ctx.reply(file=discord.File(imagepath+'final_react.gif'))
                    except Exception:
                        await ctx.reply(f'gif too big, can\'t resize enough.')
        else:
            return await ctx.reply('Something brokey')
        await resizemsg.delete()
        # reac_img = Image.open(imagepath+'dl temp')
        # font = ImageFont.truetype(imagepath+'impact.ttf', 30)


def makegif(reac_gif, text_img, img_text_height, quality):
    try:
        frames, duration = 0, 0
        images = []
        reac_width, reac_height = reac_gif.size
        while True:
            frames += 1
            duration += reac_gif.info['duration']
            final_img = Image.new('RGBA', (reac_width, img_text_height+reac_height))
            final_img.paste(text_img, (0, 0))
            final_img.paste(reac_gif, (0, img_text_height))
            images.append(final_img)
            reac_gif.seek(reac_gif.tell()+1)
    except EOFError:
        frametime = duration / frames
        images[0].save(imagepath+'final_react.gif', quality=quality, save_all=True, append_images=images[1:], duration=frametime, loop=0, disposal=2, optimize=True)
        # print(f'{frames} frames, {duration/1000}s, {frametime}ms per frame, {frames/duration*1000} fps')

async def setup(bot):
    await bot.add_cog(Images(bot))