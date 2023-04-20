import base64
import json
import math
import mpv
import sqlite3
import discord
import random
import time
import typing
import asyncio
import os
import re
import urllib.parse, urllib.request
import cogs.utils.functions as functions
from multiprocessing import Pool, cpu_count
from io import BytesIO, StringIO
from configparser import ConfigParser
# from wordcloud import WordCloud
from discord.ext import commands
from selenium import webdriver
from datetime import datetime, timedelta, date
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import InvalidSessionIdException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from collections import Counter, defaultdict
from numpy import interp
from typing import Union
from PIL import Image, ImageDraw, ImageColor

ospath = os.path.abspath(os.getcwd())
kirklinePath = rf'{ospath}/cogs/kirklines.txt'
tagpath = rf'{ospath}/cogs/tag.json'
emojipath = rf'{ospath}/emojis/'
flagpath = rf'{ospath}/cogs/flags.json'
logdatabase = rf'{ospath}/cogs/log_data.db'
config = ConfigParser()
config.read(rf'{ospath}/config.ini')
command_prefix = config['BOTCONFIG']['prefix']
IMAGE_SIZE = 854, 480
GCP_DELAY = 1
MSG_DEL_DELAY = 10
NUM_OF_RANKED_WORDS = 5

def loadLines():
    with open(kirklinePath, 'r') as f:
        lines = [line.rstrip() for line in f]
    return lines

flagInit = {
    "flags": [],
    "allowedChannels": []
}
tagInit = {
    "Servers": [
        {
            "Servername": "serverNAME",
            "ServerID": 123,
            "Tags": []
        }
    ]
}
class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        functions.checkForFile(os.path.dirname(kirklinePath), os.path.basename(kirklinePath))
        functions.checkForFile(os.path.dirname(tagpath), os.path.basename(tagpath))
        functions.checkForFile(os.path.dirname(flagpath), os.path.basename(flagpath))
        functions.checkForDir(emojipath)
        if os.stat(tagpath).st_size == 0:
            with open(tagpath, 'w') as f:
                json.dump(tagInit, f, indent=4)
        if os.stat(flagpath).st_size == 0:
            with open(flagpath, 'w') as f:
                json.dump(flagInit, f, indent=4)
        if os.stat(kirklinePath).st_size == 0:
            with open(kirklinePath, 'w') as f:
                f.write("Kirk is a based god")

    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print('fun module online')
    
    @commands.Cog.listener()
    async def on_message(self, ctx): 
        if ctx.author.bot:
            return
        if ctx.content.startswith('Kirk') or ctx.content.startswith('kirk') or ctx.content.startswith('KIRK'):
            lines = loadLines()
            await ctx.channel.send(random.choice(lines))
        
        userID = ctx.author.id
        channelID = ctx.channel.id
        
        # print (f'{ctx.created_at}')
        
        with open(flagpath, 'r') as flagins:
            flagdata = json.load(flagins)
        
        for allowedChannels in flagdata['allowedChannels']:
            if channelID == allowedChannels["channelID"]:
                for flags in flagdata['flags']:
                    if userID == flags["memberID"]:
                        try:
                            await ctx.add_reaction(flags["emoji"])
                        except:
                            userNICK = ctx.author.display_name
                            newNICK = userNICK[:28] + '🌈⚧️'
                            await ctx.author.edit(nick=newNICK)
                            
                            with open(flagpath, 'r') as flagin:
                                flagdata = json.load(flagin)  
                            
                            for idx, flags in enumerate(flagdata['flags']):
                                if flags["memberID"] == userID:
                                    del flagdata['flags'][idx]
                                    break
                            
                            with open(flagpath, 'w') as flagout:
                                json.dump(flagdata, flagout, indent=4)  
                        break
                    # else:
                    #     if random.randint(0, 10) == 1:
                    #         emojiList = [emoji for emoji in ctx.guild.emojis]
                    #         await ctx.add_reaction(random.choice(emojiList))
                else:
                    if random.randint(0, 30) == 1:
                        emojiList = [emoji for emoji in ctx.guild.emojis]
                        await ctx.add_reaction(random.choice(emojiList))                    
                    break
        else:
            pass
    
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        '''See delay of the bot'''
        async with ctx.typing():
            before = time.monotonic()
            before_ws = int(round(self.bot.latency * 1000, 1))
            message = await ctx.send("🏓 Pong")
            ping = (time.monotonic() - before) * 1000
            # await ctx.send(f'plong {round(self.bot.latency * 1000)} ms')
            await message.edit(content=f"🏓 WS: {before_ws}ms  |  REST: {int(ping)}ms")
    
    @commands.command(aliases=['8ball'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _8ball(self, ctx, *, question: str):
        '''[_8ball] [8ball]. Ask a question and get a response'''
        responses = ["It is certain.",
                    "It is decidedly so.",
                    "Without a doubt.",
                    "Yes - definitely.",
                    "You may rely on it.",
                    "As I see it, yes.",
                    "Most likely.",
                    "Outlook good.",
                    "Yes.",
                    "Signs point to yes.",
                    "Reply hazy, try again.",
                    "Ask again later.",
                    "Better not tell you now.",
                    "Cannot predict now.",
                    "Concentrate and ask again.",
                    "Don't count on it.",
                    "My reply is no.",
                    "My sources say no.",
                    "Outlook not so good.",
                    "Very doubtful."]
        async with ctx.typing():
            await ctx.send(f'question: {question}\n Answer: {random.choice(responses)}')
    
    @commands.command(name='checkem', aliases=['check', 'c'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def checkem(self, ctx):
        '''[checkem] [check] [c]. Check random number for dubs trips etc.'''
        async with ctx.typing():
            number = random.randint(100000000, 999999999)
            numlist = list(map(int, str(number)))
            
            if numlist[8] != numlist[7]:
                result = 'nothing, try again'
                colour = discord.Colour.red()
            if numlist[8] == numlist[7]:
                result = 'dubs congrats'
                colour = discord.Colour.green()
            if numlist[8] == numlist[7] ==  numlist[6]:
                result = 'trips congrats'
                colour = discord.Colour.green()
            if numlist[8] == numlist[7] == numlist[6] == numlist[5]:
                result = 'quads congrats'
                colour = discord.Colour.green()
            if numlist[8] == numlist[7] == numlist[6] == numlist[5] == numlist[4]:
                result = 'quints congrats'
                colour = discord.Colour.green()
            if numlist[8] == numlist[7] == numlist[6] == numlist[5] == numlist[4] == numlist[3]:
                result = 'sexts congrats'
                colour = discord.Colour.green()
            if numlist[8] == numlist[7] == numlist[6] == numlist[5] == numlist[4] == numlist[3] == numlist[2]:
                result = 'septs congrats'
                colour = discord.Colour.green()
            if numlist[8] == numlist[7] == numlist[6] == numlist[5] == numlist[4] == numlist[3] == numlist[2] == numlist[1]:
                result = 'octs congrats'
                colour = discord.Colour.green()
            if numlist[8] == numlist[7] == numlist[6] == numlist[5] == numlist[4] == numlist[3] == numlist[2] == numlist[1] == numlist[0]:
                result = 'nons congrats'
                colour = discord.Colour.green()
            
            valuefield1 = f'You got {result}.'         
            embedVar = discord.Embed(color=colour)
            embedVar.add_field(name=number, value=valuefield1, inline=False)
            await ctx.send(embed=embedVar)

    @commands.command(name='bigletter', aliases=['em'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def bigletter(self, ctx, *, input:str):
        '''[bigletter] [em]. Types you messages in letter emojis. '''
        await ctx.message.delete()
        emojis = []
        async with ctx.typing():
            for text in input.lower():
                if text.isdecimal():
                    numToWord = {'0':'zero', '2':'two', '3':'three', '4':'four', '5':'five', '6':'six', '7':'seven', '8':'eight', '9':'nine'}
                    emojis.append(f':{numToWord.get(text)}:')
                elif text.isalpha():
                    emojis.append(f':regional_indicator_{text}:')
                elif text == ('?'):
                    emojis.append(f':question:')
                else:
                    emojis.append(text)
            await ctx.send(''.join(emojis))
    
    @commands.command(name='braille', aliases=['br'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def braille(self, ctx, *, input:str):
        '''[braille] [br]. Converts you message to braille so blind people can read it.'''
        async with ctx.typing():
            braille = input.lower().replace("a", "⠁").replace("b", "⠃").replace("c", "⠉").replace("d", "⠙").replace("e", "⠑").replace("f", "⠋").replace("g", "⠛").replace("h", "⠓").replace("i", "⠊").replace("j", "⠚").replace("k", "⠅").replace("l", "⠅").replace("m", "⠍").replace("n", "⠝").replace("o", "⠕").replace("p", "⠏").replace("q", "⠟").replace("r", "⠗").replace("s", "⠎").replace("t", "⠞").replace("u", "⠥").replace("v", "⠧").replace("w", "⠺").replace("x", "⠭").replace("y", "⠽").replace("z", "⠵")
            await ctx.send(f'For the blind: {braille}')
    
    @commands.command(name='youtube', aliases=['yt'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def youtube(self, ctx, *, search:str):
        '''[youtube] [yt]. Posts youtube vid from search.'''
        async with ctx.typing():
            query_string = urllib.parse.urlencode({'search_query':search})
            html_content = urllib.request.urlopen('https://www.youtube.com/results?' + query_string)
            search_results = re.findall(r"watch\?v=(\S{11})", html_content.read().decode())
            cur_page = 0
            message = await ctx.send('https://www.youtube.com/watch?v=' + search_results[cur_page])
            
            await message.add_reaction("◀️")
            await message.add_reaction("▶️")
            # await message.add_reaction("\U0001f50d") #Magnifying glass
            await message.add_reaction("#\uFE0F\u20E3") #Number sign
            await message.add_reaction(f"{cur_page+1}\uFE0F\u20E3") #Page number
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]
                # This makes sure nobody except the command sender can interact with the "menu"
            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=15, check=check)
                    
                    if str(reaction.emoji) == "▶️" and cur_page != 8:
                        await message.remove_reaction(f'{cur_page+1}\uFE0F\u20E3', self.bot.user)
                        cur_page += 1
                        await message.edit(content='https://www.youtube.com/watch?v=' + search_results[cur_page])
                        await message.add_reaction(f"{cur_page+1}\uFE0F\u20E3")
                        await message.remove_reaction(reaction, user)
                    
                    elif str(reaction.emoji) == "◀️" and cur_page > 0:
                        await message.remove_reaction(f'{cur_page+1}\uFE0F\u20E3', self.bot.user)                    
                        cur_page -= 1
                        await message.edit(content='https://www.youtube.com/watch?v=' + search_results[cur_page])
                        await message.add_reaction(f"{cur_page+1}\uFE0F\u20E3")                    
                        await message.remove_reaction(reaction, user)
                    
                    else:
                        await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    await message.remove_reaction('▶️', self.bot.user)
                    await message.remove_reaction('◀️', self.bot.user)
                    await message.remove_reaction('#\uFE0F\u20E3', self.bot.user)
                    await message.remove_reaction(f'{cur_page+1}\uFE0F\u20E3', self.bot.user)
                    break
    
    @commands.group(name='gcp', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def gcp_dot_base(self, ctx):
        async with ctx.typing():
            byteiogcpdot = BytesIO()
            options = webdriver.ChromeOptions()
            options.headless = True
            driver = webdriver.Chrome(options=options)
            driver.set_window_size(1500,750)
            driver.get("https://gcpdot.com/gcpchart.php")
            time.sleep(GCP_DELAY)
            
            chart_screenshot_base64 = driver.get_screenshot_as_base64()
            chart_file = BytesIO(base64.b64decode(chart_screenshot_base64))
            
            try:
                chart_height = float(driver.find_element(By.ID, 'gcpChartShadow').get_attribute("height")) + 20
                dot = driver.find_elements(By.XPATH, '/html/body/div/div')[-1]
                dot_id = dot.get_attribute('id')
                dot_height = driver.find_element(By.ID, dot_id).value_of_css_property('top')
                dot_height = float(dot_height.replace('px', ''))
                
                # Map dot height into domain [0.0...1.0] rather than raw css property value
                high = 0
                high = interp(float(dot_height), [0, chart_height], [0.0, 1.0])
                
                if high == 0:
                    color = '#505050'
                    gcpStatus = 'It is hivemind time!'
                    colorname = 'grey'
                else:
                    intervals = {
                        (0.00, 0.01): ('#FFA8C0', 'Significantly large network variance. Suggests broadly shared coherence of thought and emotion. The index is less than 1%', 'pink'),
                        (0.01, 0.05): ('#FF0000', 'Significantly large network variance. Suggests broadly shared coherence of thought and emotion. The index is between 1% and 5%', 'red'),
                        (0.05, 0.10): ('#FFB82E', 'Strongly increased network variance. May be chance fluctuation, with the index between 5% and 10%', 'orange'),
                        (0.10, 0.40): ('#FFFA40', 'Slightly increased network variance. Probably chance fluctuation. The index is between 10% and 40%', 'yellow'),
                        (0.40, 0.90): ('#00FF00', 'Normally random network variance. This is average or expected behavior. The index is between 40% and 90%', 'green'),
                        (0.90, 0.95): ('#00FFFF', 'Small network variance. Probably chance fluctuation. The index is between 90% and 95%', 'cyan'),
                        (0.95, 0.99): ('#0000FF', 'Significantly small network variance. Suggestive of deeply shared, internally motivated group focus. The index is between 95% and 99%', 'blue'),
                        (0.99, 1.00): ('#4B0082', 'Significantly small network variance. Suggestive of deeply shared, internally motivated group focus. The index is above 99%', 'indigo')
                    }

                    for interval, (interval_color, interval_status, interval_colorname) in intervals.items():
                        if interval[0] <= high < interval[1]:
                            color = interval_color
                            gcpStatus = interval_status
                            colorname = interval_colorname
                            break
                    else:
                        color = '#505050'
                        gcpStatus = 'The Dot is broken!'
                        colorname = 'grey'
            
            except(TimeoutException, InvalidSessionIdException, Exception) as e:
                print("Sick exception: " + str(e))
                driver.close()
                raise e
            driver.close()
            
            circleSize = 200
            newImage = Image.new('RGBA', (circleSize, circleSize), (0, 0, 0, 0))
            draw = ImageDraw.Draw(newImage)
            draw.ellipse((0, 0, circleSize, circleSize), fill = color, outline ='white')
            newImage.save(byteiogcpdot, format='PNG')
            byteiogcpdot.seek(0)
            
            pics = [discord.File(byteiogcpdot, filename='gcpdot.png'), discord.File(chart_file, filename='wholechart.png')]
            colorint = int(color[1:], 16)
            gcppercent = round(high * 100, 2)
            embed = discord.Embed(title=f'Currently the GCP Dot is {colorname} at {gcppercent}%.', description=gcpStatus, color=colorint)
            embed.set_image(url='attachment://wholechart.png')
            embed.set_thumbnail(url='attachment://gcpdot.png')
            embed.set_footer(text=f'Use {command_prefix}gcp full for an explanation of all the colours.')
            await ctx.reply(embed=embed, files=pics)
    
    @gcp_dot_base.command(name='full', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def gcp_dot_full(self, ctx):
        async with ctx.typing():
            byteiogcpdot = BytesIO()
            options = webdriver.ChromeOptions()
            options.headless = True
            driver = webdriver.Chrome(options=options)
            driver.set_window_size(1000,500)
            driver.get("https://gcpdot.com/gcpchart.php")
            time.sleep(GCP_DELAY)
            
            chart_screenshot_base64 = driver.get_screenshot_as_base64()
            chart_file = BytesIO(base64.b64decode(chart_screenshot_base64))
            
            try:
                chart_height = float(driver.find_element(By.ID, 'gcpChartShadow').get_attribute("height")) + 20
                dot = driver.find_elements(By.XPATH, '/html/body/div/div')[-1]
                dot_id = dot.get_attribute('id')
                dot_height = driver.find_element(By.ID, dot_id).value_of_css_property('top')
                dot_height = float(dot_height.replace('px', ''))
                
                # Map dot height into domain [0.0...1.0] rather than raw css property value
                high = 0
                high = interp(float(dot_height), [0, chart_height], [0.0, 1.0])
                
                if high == 0:
                    color = '#505050'
                    gcpStatus = 'It is hivemind time!'
                    colorname = 'grey'
                else:
                    intervals = {
                        (0.00, 0.01): ('#FFA8C0', 'Significantly large network variance. Suggests broadly shared coherence of thought and emotion. The index is less than 1%', 'pink'),
                        (0.01, 0.05): ('#FF0000', 'Significantly large network variance. Suggests broadly shared coherence of thought and emotion. The index is between 1% and 5%', 'red'),
                        (0.05, 0.10): ('#FFB82E', 'Strongly increased network variance. May be chance fluctuation, with the index between 5% and 10%', 'orange'),
                        (0.10, 0.40): ('#FFFA40', 'Slightly increased network variance. Probably chance fluctuation. The index is between 10% and 40%', 'yellow'),
                        (0.40, 0.90): ('#00FF00', 'Normally random network variance. This is average or expected behavior. The index is between 40% and 90%', 'green'),
                        (0.90, 0.95): ('#00FFFF', 'Small network variance. Probably chance fluctuation. The index is between 90% and 95%', 'cyan'),
                        (0.95, 0.99): ('#0000FF', 'Significantly small network variance. Suggestive of deeply shared, internally motivated group focus. The index is between 95% and 99%', 'blue'),
                        (0.99, 1.00): ('#4B0082', 'Significantly small network variance. Suggestive of deeply shared, internally motivated group focus. The index is above 99%', 'indigo')
                    }
                    
                    for interval, (interval_color, interval_status, interval_colorname) in intervals.items():
                        if interval[0] <= high < interval[1]:
                            color = interval_color
                            gcpStatus = interval_status
                            colorname = interval_colorname
                            break
                    else:
                        color = '#505050'
                        gcpStatus = 'The Dot is broken!'
                        colorname = 'grey'
            
            except(TimeoutException, InvalidSessionIdException, Exception) as e:
                print("Sick exception: " + str(e))
                driver.close()
                raise e
            driver.close()
            
            circleSize = 200
            newImage = Image.new('RGBA', (circleSize, circleSize), (0, 0, 0, 0))
            draw = ImageDraw.Draw(newImage)
            draw.ellipse((0, 0, circleSize, circleSize), fill = color, outline ='white')
            newImage.save(byteiogcpdot, format='PNG')
            byteiogcpdot.seek(0)
            
            pics = [discord.File(byteiogcpdot, filename='gcpdot.png'), discord.File(chart_file, filename='wholechart.png')]
            colorint = int(color[1:], 16)
            gcppercent = round(high * 100, 2)
            embed = discord.Embed(title=f'Currently the GCP Dot is {colorname} at {gcppercent}%.', description=gcpStatus, color=colorint)
            embed.set_image(url='attachment://wholechart.png')
            embed.set_thumbnail(url='attachment://gcpdot.png')
            embed.add_field(name="Blue ", value='Significantly small network variance. Suggestive of deeply shared, internally motivated group focus. The index is above 95%', inline=True)
            embed.add_field(name="Teal ", value='Small network variance. Probably chance fluctuation. The index is between 90% and 95%', inline=True)
            embed.add_field(name="Green ", value='Normally random network variance. This is average or expected behavior. The index is between 40% and 90%', inline=True)
            embed.add_field(name="Yellow ", value='Slightly increased network variance. Probably chance fluctuation. The index is between 10% and 40%', inline=True)
            embed.add_field(name="Orange ", value='Strongly increased network variance. May be chance fluctuation, with the index between 5% and 10%', inline=True)
            embed.add_field(name="Red ", value='Significantly large network variance. Suggests broadly shared coherence of thought and emotion. The index is less than 5%', inline=True)
            await ctx.reply(embed=embed, files=pics)        
    
    @commands.has_role('Tag')
    @commands.group(name='tag', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tag_base(self, ctx, member:discord.Member):
        serverNAME = ctx.guild.name
        serverID = ctx.guild.id
        userNAME = member.name
        userID = member.id
        newserver = {
            "Servername": serverNAME,
            "ServerID": serverID,
            "Tags":[{
                "Tagged username": userNAME,
                "Tagged userid": userID,          
                }]
            }
        newtag = {
            "Tagged user": userNAME,
            "Tagged userid": userID,
        }
        
        with open(tagpath, 'r') as tagin:
            tagdata = json.load(tagin)
        async with ctx.typing():
            try:
                for servers in tagdata['Servers']:
                    if serverID == servers["ServerID"]:
                        servers["Tags"].append(newtag)
                        raise StopIteration
                tagdata["Servers"].append(newserver)                   
            except StopIteration:
                pass
            
            with open(tagpath, 'w') as tagout:
                json.dump(tagdata, tagout, indent=4)
            
            role = discord.utils.get(ctx.guild.roles, name='Tag')
            await member.add_roles(role)
            await ctx.author.remove_roles(role)
            await ctx.channel.send(f'{member.mention} got tagged!')

    @tag_base.command(name='get', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tag_get(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name='Tag')
        guild = self.bot.get_guild(ctx.guild.id)
        async with ctx.typing():
            for members in guild.members:
                if role in members.roles:
                    await ctx.channel.send(f'{members.mention} is tagged!')
    
    @commands.has_permissions(administrator=True)
    @commands.command(name='whocare')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def who_care(self, ctx):
        if ctx.message.reference:
            await ctx.message.delete()
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            #This spells who care(s). Can't do it the bigletter command way because multiple of the same react emoji is not possible.
            await message.add_reaction('\U0001f1fc')
            await message.add_reaction('\U0001f1ed')
            await message.add_reaction('\U0001f1f4')
            await message.add_reaction('\U0001f1e8')
            await message.add_reaction('\U0001f1e6')
            await message.add_reaction('\U0001f1f7')
            await message.add_reaction('\U0001f1ea')
            # await message.add_reaction('\U0001f1f8')
        else:
            await ctx.message.delete()
    
    @commands.has_permissions(administrator=True)
    @commands.command(aliases=["p"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def probe(self, ctx):
        await ctx.message.delete()
        if ctx.message.reference:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await message.add_reaction('✝')
            await message.remove_reaction('✝', self.bot.user)
    
    @commands.has_permissions(administrator=True)
    @commands.group(name='flag', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flag_base(self, ctx, member:discord.Member, emoji:str):
        re_emoji_custom = r'<a?:.+?:\d{18,19}>'
        re_emoji_generic = re.compile("[""\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                        "\U0001F300-\U0001F5FF"  # symbols & pictographs
                                        "\U0001F600-\U0001F64F"  # emoticons
                                        "\U0001F680-\U0001F6FF"  # transport & map symbols
                                        "\U0001F700-\U0001F77F"  # alchemical symbols
                                        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
                                        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                                        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                                        "\U0001FA00-\U0001FA6F"  # Chess Symbols
                                        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                                        "\U00002702-\U000027B0"  # Dingbats
                                        "\U000024C2-\U0001F251" 
                                        "]+")
        
        async with ctx.typing():
            if (re.match(re_emoji_custom, emoji)) or (re.match(re_emoji_generic, emoji)):
                with open(flagpath, 'r') as flagin:
                    flagdata = json.load(flagin)
                
                member_flag = {"memberID":member.id, "emoji":emoji}
                for flags in flagdata['flags']:
                    if flags["memberID"] == member.id:
                        flags["emoji"] = emoji
                        break
                else:
                    flagdata["flags"].append(member_flag)
                
                with open(flagpath, 'w') as flagout:
                    json.dump(flagdata, flagout, indent=4)
                
                response = await ctx.reply(f'Flag added! {emoji} will now appear under every messsage send by {member.display_name}')
            else:
                response = await ctx.reply(f'{emoji} not recognized as an emoji!')
        await response.delete(delay=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.has_permissions(administrator=True)
    @flag_base.command(name='remove', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flag_remove(self, ctx, member:discord.Member):
        with open(flagpath, 'r') as flagin:
            flagdata = json.load(flagin)  
        
        async with ctx.typing():
            for idx, flags in enumerate(flagdata['flags']):
                if flags["memberID"] == member.id:
                    del flagdata['flags'][idx]
                    response = await ctx.reply(f'Removed flag from {member.display_name}')
                    break
            else:
                response = await ctx.reply(f'{member.display_name} has no flag!')
        
        with open(flagpath, 'w') as flagout:
            json.dump(flagdata, flagout, indent=4)        
        await response.delete(delay=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.has_permissions(administrator=True)
    @flag_base.command(name='toggle', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flag_toggle(self, ctx):
        with open(flagpath, 'r') as flagin:
            flagdata = json.load(flagin)  
        
        async with ctx.typing():
            allowed_channel = {"channelID":ctx.channel.id}
            for idx, allowedChannels in enumerate(flagdata['allowedChannels']):
                if allowedChannels['channelID'] == ctx.channel.id:
                    del flagdata['allowedChannels'][idx]
                    response = await ctx.reply(f'Removed {ctx.channel.name} from the allowed channels list')
                    break
            else:
                flagdata["allowedChannels"].append(allowed_channel)
                response = await ctx.reply(f'Added {ctx.channel.name} to the allowed channels list')
        
        with open(flagpath, 'w') as flagout:
            json.dump(flagdata, flagout, indent=4)        
        await response.delete(delay=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.has_permissions(administrator=True)
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def emojis(self, ctx):
        # await ctx.message.reply(f'Copy of all emojis in the server:\n{" ".join([str(emoji) for emoji in ctx.guild.emojis])}\n\nCopy of all emojis bot can access:\n{" ".join([str(emoji) for emoji in self.bot.emojis])}\n\nAll emojis saved.')
        await ctx.send('Tried to save all emojis bot can access')
        for emoji in self.bot.emojis:
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            await emoji.save(rf'{emojipath}{emoji.name}_{now}.png')    
    
    @tag_base.error
    async def tag_base_handeler(self, ctx, error):
        if (discord.utils.get(ctx.guild.roles, name='Tag')) is None:
            await ctx.guild.create_role(name='Tag')
            await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, name='Tag'))
            
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(f'To tag use {command_prefix}tag @user')
    
    @commands.group(name='wordcount', aliases=["wc"], invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wordcount_base(self, ctx, member:Union[discord.Member, int], input_word:str=None):
        if isinstance(member, discord.Member):
            user_id = member.id
        else:
            user_id = member
        if input_word is not None:
            input_word = input_word.lower()
        
        con = sqlite3.connect(f'{ospath}/cogs/log_data.db')
        cur = con.cursor()
        cur.execute('SELECT user_id, message FROM log_data WHERE server_id = ?', (ctx.guild.id,))
        userid_messages = cur.fetchall()
        
        grouped = defaultdict(lambda: {'id': None, 'words': [], 'word_counts': Counter()})
        for id, value in userid_messages:
            grouped[id]['id'] = id
            grouped[id]['words'].extend(value.lower().split())
            grouped[id]['word_counts'].update(value.lower().split())
        
        if user_id not in grouped:
            await ctx.send(f"{member} has no recorded messages")
        else:
            data = grouped[user_id]
            try:
                display_name = ctx.guild.get_member(user_id).display_name
            except Exception:
                cur.execute('SELECT username FROM log_data WHERE server_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1', (ctx.guild.id, user_id))
                result = cur.fetchone()
                if result:
                    display_name = result[0]
                else:
                    msg = await ctx.reply(f'No user with ID {user_id} found in {ctx.guild.name}')
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
            
            top_words = [word for word, count in data['word_counts'].most_common(NUM_OF_RANKED_WORDS)]
            if input_word is None:
                embed = discord.Embed(title=f"Top {NUM_OF_RANKED_WORDS} used words for {display_name} in {ctx.guild.name}", color=0x00ff00)
                embed.add_field(name=f"Rank", value='\n'.join(f"> #{i+1}" for i in range(NUM_OF_RANKED_WORDS)), inline=True)
                embed.add_field(name=f"Word", value='\n'.join(f"> {word}" for word in top_words), inline=True)
                embed.add_field(name=f"Occurrence", value='\n'.join(f"> {count}" for word, count in data['word_counts'].most_common(NUM_OF_RANKED_WORDS)), inline=True)
            else:
                count = data['word_counts'].get(input_word, 0)
                embed = discord.Embed(title=f"{display_name}'s use of '{input_word[:128]}' in {ctx.guild.name}", color=0x00ff00)
                embed.add_field(name=f"Occurrences of {input_word}", value=f"{count}", inline=False)
            embed.set_footer(text=f'Wordcount record {daysago()} days old.')
            await ctx.send(embed=embed)
        cur.close()
        con.close()

    @wordcount_base.error
    async def wordcount_base_error(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            msg = await ctx.reply('The second argument needs to be either: [`@user` or `ID`]'+f', `server`, or `channel`. Refer to `{command_prefix}help fun wordcount` for details on all the possible commands.')
            ctx._ignore_ = True
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @wordcount_base.command(name='server', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wordcount_server(self, ctx, input_word:str=None):
        con = sqlite3.connect(f'{ospath}/cogs/log_data.db')
        cur = con.cursor()
        cur.execute('SELECT user_id, message FROM log_data WHERE server_id = ?', (ctx.guild.id,))
        userid_messages = cur.fetchall()
        
        def getusername(userid):
            cur.execute('SELECT username FROM log_data WHERE server_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1', (ctx.guild.id, userid))
            display_name = cur.fetchone()
            return display_name[0]
        
        if input_word is not None:
            input_word = input_word.lower()
        
        grouped = defaultdict(lambda: {'id': None, 'words': [], 'word_counts': Counter()})
        for id, value in userid_messages:
            grouped[id]['id'] = id
            grouped[id]['words'].extend(value.lower().split())
            grouped[id]['word_counts'].update(value.lower().split())
        
        if input_word is None:
            for user_data in grouped.values():
                user_data['word_count'] = sum(user_data['word_counts'].values())
            sorted_users = sorted(grouped.values(), key=lambda x: x['word_count'], reverse=True)
            total_counts = Counter()
            for user_data in sorted_users:
                total_counts.update(user_data['word_counts'])
            top_words = [word for word, count in sorted_users[0]['word_counts'].most_common(NUM_OF_RANKED_WORDS)]
            embed = discord.Embed(title=f"Top {NUM_OF_RANKED_WORDS} used words in {ctx.guild.name}", color=0xff0000)
            embed.add_field(name=f"Rank", value='\n'.join(f"> #{i+1}" for i in range(NUM_OF_RANKED_WORDS)), inline=True)
            embed.add_field(name=f"Word", value='\n'.join(f"> {word[:1020]}" for word in top_words), inline=True)
            embed.add_field(name=f"Occurrence", value='\n'.join(f"> {total_counts[word]}" for word in top_words), inline=True)
        
        else:
            user_word_counts = {}
            for user_data in grouped.values():
                if input_word in user_data['word_counts']:
                    user_word_counts[user_data['id']] = user_data['word_counts'][input_word]
            if not user_word_counts:
                await ctx.send(f"No user in {ctx.guild.name} used the word '{input_word}'.")
                return
            sorted_users = sorted(user_word_counts.items(), key=lambda x: x[1], reverse=True)
            num_users = min(NUM_OF_RANKED_WORDS, len(sorted_users))
            embed = discord.Embed(title=f"Top {num_users} users who used '{input_word[:128]}' in {ctx.guild.name}", color=0xff0000) #27, 100 guildname
            embed.add_field(name=f"Rank", value='\n'.join(f"> #{i+1}" for i in range(num_users)), inline=True)
            embed.add_field(name=f"User", value='\n'.join(f"> {ctx.guild.get_member(user_id).display_name}" if ctx.guild.get_member(user_id) else getusername(user_id) for user_id, count in sorted_users[:num_users]), inline=True)
            embed.add_field(name=f"Occurrence", value='\n'.join(f"> {str(count)}" for user_id, count in sorted_users[:num_users]), inline=True)
        
        embed.set_footer(text=f'Wordcount record {daysago()} days old.')
        await ctx.send(embed=embed)
        cur.close()
        con.close()
    
    @wordcount_base.command(name='channel', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wordcount_channel(self, ctx, input_word:str=None):
        con = sqlite3.connect(f'{ospath}/cogs/log_data.db')
        cur = con.cursor()
        cur.execute('SELECT user_id, message FROM log_data WHERE channel_id = ?', (ctx.channel.id,))
        userid_messages = cur.fetchall()
        
        def getusername(userid):
            cur.execute('SELECT username FROM log_data WHERE server_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1', (ctx.guild.id, userid))
            display_name = cur.fetchone()
            return display_name[0]
        
        if input_word is not None:
            input_word = input_word.lower()
        
        grouped = defaultdict(lambda: {'id': None, 'words': [], 'word_counts': Counter()})
        for id, value in userid_messages:
            grouped[id]['id'] = id
            grouped[id]['words'].extend(value.lower().split())
            grouped[id]['word_counts'].update(value.lower().split())
        
        if input_word is None:
            for user_data in grouped.values():
                user_data['word_count'] = sum(user_data['word_counts'].values())
            sorted_users = sorted(grouped.values(), key=lambda x: x['word_count'], reverse=True)
            total_counts = Counter()
            for user_data in sorted_users:
                total_counts.update(user_data['word_counts'])
            top_words = [word for word, count in sorted_users[0]['word_counts'].most_common(NUM_OF_RANKED_WORDS)]
            embed = discord.Embed(title=f"Top {NUM_OF_RANKED_WORDS} used words in {ctx.channel.name}", color=0x0000ff)
            embed.add_field(name=f"Rank", value='\n'.join(f"> #{i+1}" for i in range(NUM_OF_RANKED_WORDS)), inline=True)
            embed.add_field(name=f"Word", value='\n'.join(f"> {word[:1020]}" for word in top_words), inline=True)
            embed.add_field(name=f"Occurrence", value='\n'.join(f"> {total_counts[word]}" for word in top_words), inline=True)
        
        else:
            user_word_counts = {}
            for user_data in grouped.values():
                if input_word in user_data['word_counts']:
                    user_word_counts[user_data['id']] = user_data['word_counts'][input_word]
            if not user_word_counts:
                await ctx.send(f"No user in {ctx.channel.name} used the word '{input_word}'.")
                return
            sorted_users = sorted(user_word_counts.items(), key=lambda x: x[1], reverse=True)
            num_users = min(NUM_OF_RANKED_WORDS, len(sorted_users))
            embed = discord.Embed(title=f"Top {num_users} users who used '{input_word[:128]}' in {ctx.channel.name}", color=0x0000ff)
            embed.add_field(name=f"Rank", value='\n'.join(f"> #{i+1}" for i in range(num_users)), inline=True)
            embed.add_field(name=f"User", value='\n'.join(f"> {ctx.guild.get_member(user_id).display_name}" if ctx.guild.get_member(user_id) else getusername(user_id) for user_id, count in sorted_users[:num_users]), inline=True)
            embed.add_field(name=f"Occurrence", value='\n'.join(f"> {str(count)}" for user_id, count in sorted_users[:num_users]), inline=True)
        
        embed.set_footer(text=f'Wordcount record {daysago()} days old.')
        await ctx.send(embed=embed)
        cur.close()
        con.close()
    
    # @commands.command(aliases=["fish"])
    # @commands.cooldown(1, 5, commands.BucketType.user)
    # async def fishtank_monitor(self, ctx):
    #     streams = ['https://d27j2syygqshcy.cloudfront.net/live/bedroom-1/chunks.m3u8',
    #             'https://d27j2syygqshcy.cloudfront.net/live/bedroom-2/chunks.m3u8',
    #             'https://d27j2syygqshcy.cloudfront.net/live/bedroom-3/chunks.m3u8',
    #             'https://d27j2syygqshcy.cloudfront.net/live/bedroom-4/chunks.m3u8',
    #             'https://d27j2syygqshcy.cloudfront.net/live/living-room/chunks.m3u8',
    #             'https://d27j2syygqshcy.cloudfront.net/live/kitchen/chunks.m3u8',
    #             'https://d27j2syygqshcy.cloudfront.net/live/laundry-room/chunks.m3u8',
    #             'https://d27j2syygqshcy.cloudfront.net/live/garage/chunks.m3u8',
    #             'https://d27j2syygqshcy.cloudfront.net/live/hallway-upstairs/chunks.m3u8',
    #             'https://d27j2syygqshcy.cloudfront.net/live/hallway-downstairs/chunks.m3u8']
        
    #     streams_matrix = mpv_screenshots(streams)
    #     await ctx.reply(file=discord.File(streams_matrix, 'fishtank_monitor.jpg'))
    
async def setup(bot):
    await bot.add_cog(Fun(bot))

def daysago():
    con = sqlite3.connect(f'{ospath}/cogs/log_data.db')
    cur = con.cursor()
    cur.execute('SELECT unix_time FROM log_data ORDER BY id ASC LIMIT 1', ())
    unix_time = cur.fetchone()
    timestamp = datetime.fromtimestamp(unix_time[0])
    current_time = datetime.now()
    time_since = current_time - timestamp
    days_since = time_since.days
    return days_since

def mpv_screenshot(stream):
    player = mpv.MPV(screenshot_format='jpeg', vo='null', hwdec='yes', screenshot_sw='yes')
    player.play(stream)
    player.wait_until_playing()
    screenshot = player.screenshot_raw()
    player.terminate()
    return screenshot

def mpv_screenshots(streams):
    streams_matrix = BytesIO()
    count = len(streams)
    srw = math.ceil(math.sqrt(count))
    result_image = Image.new('RGB', (IMAGE_SIZE[0] * srw, IMAGE_SIZE[1] * (srw-1)))
    
    with Pool(cpu_count()//2) as pool:
        screenshots = pool.map(mpv_screenshot, streams)
    
    for i, screenshot in enumerate(screenshots):
        screenshot.thumbnail(IMAGE_SIZE, Image.Resampling.LANCZOS)
        result_image.paste(screenshot, (IMAGE_SIZE[0] * (i % srw), IMAGE_SIZE[1] * (i // srw)))
        result_image.save(streams_matrix, format='JPeG', quality=100)
        streams_matrix.seek(0)
    
    return streams_matrix







    # @commands.command(aliases=["sc"])
    # @commands.cooldown(1, 5, commands.BucketType.user)
    # async def server_conciousness(self, ctx):
    #     # await ctx.send("")
    #     messagelist = []
    #     for channel in ctx.guild.channels:
    #         if isinstance(channel, discord.TextChannel):
    #             # messages = [message.content async for message in channel.history(after=datetime.now()-timedelta(days=1), oldest_first=True)]
    #             async for message in channel.history(after=datetime.now()-timedelta(days=100), oldest_first=True):
    #                 messagelist.append(message.content)
    #     # print (messages)
    #     print (messagelist)



    # @commands.command(name='wordcloud', aliases=["wc"])
    # @commands.cooldown(1, 5, commands.BucketType.user)
    # async def wordcloud(self, ctx, server_or_channel:str, limit:int=100000):
    #     byteiowordcloud = BytesIO()
    #     messages = []
    #     wordlist = []
    #     links = r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,10}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'
    #     async with ctx.typing():
    #         if server_or_channel.lower() == 'server':
    #             for channel in ctx.guild.text_channels:
    #                 async for message in channel.history(limit=limit, oldest_first=True):
    #                     # messages.append(message)
    #                     wordlist += message.content.split()
                
    #         elif server_or_channel.lower() == 'channel':
    #             async for message in ctx.channel.history(limit=limit, oldest_first=True):
    #                 # messages.append(message)
    #                 wordlist += message.content
    #                 with open (r'./cogs/wordlist.txt', 'w') as wordcloudfile:
    #                     wordcloudfile.write(wordlist)
                
    #         else:
    #             await ctx.reply(f'Specify either "server" or "channel" as the first argument')
    #             return
            
    #         # for word in wordlist:
    #         #     if re.match(links, word):
    #         #         wordlist.remove(word)
            
    #         # for message in messages:
    #         #     # if message.author.bot:
    #         #     #     continue
    #         #     # sentence = functions.filter(message.content)
    #         #     nolinks = re.sub(links, '', message.content)
    #         #     wordlist += nolinks.split()
            
    #         # data5 = Counter(wordlist)
    #         wordcloud = WordCloud(width=3840, height=2160, colormap='hsv').generate(' '.join(wordlist))
    #         # wordcloud = WordCloud(width=3840, height=2160, colormap='hsv').generate_from_frequencies(data5)
    #         wordcloudImage = wordcloud.to_image()
    #         wordcloudImage.save(byteiowordcloud, format='PNG')
    #         byteiowordcloud.seek(0)
    #         await ctx.send(file=discord.File(byteiowordcloud, filename='wordcloud.png'))
    