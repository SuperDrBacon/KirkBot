import asyncio
import base64
import json
import math
import os
import random
import re
import time
import urllib.parse
import urllib.request
import aiosqlite
import discord
import mpv

from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import BytesIO
from multiprocessing import Pool, cpu_count
from typing import Union
from discord.ext import commands
from numpy import interp
from PIL import Image, ImageDraw
from selenium import webdriver
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from cogs.utils.constants import (
    ARCHIVE_DATABASE, BOTVERSION, COMMAND_PREFIX,
    EMOJIPATH, FLAGPATH, GCP_DELAY, IMAGE_SIZE,
    MSG_DEL_DELAY, NUM_OF_RANKED_WORDS)

flagInit = {
    "flags": [],
    "allowedChannels": []
}
class Fun(commands.Cog):
    '''
    This module houses all the fun commands.
    '''
    def __init__(self, bot):
        self.bot = bot
        
        if os.stat(FLAGPATH).st_size == 0:
            with open(FLAGPATH, 'w') as f:
                json.dump(flagInit, f, indent=4)
    
    async def daysago(self):
        async with aiosqlite.connect(ARCHIVE_DATABASE) as con:
            async with con.execute('SELECT unix_time FROM archive_data ORDER BY id ASC LIMIT 1') as cur:
                unix_time = await cur.fetchone()
                if not unix_time:
                    return 0
            
            timestamp = datetime.fromtimestamp(unix_time[0])
            current_time = datetime.now()
            time_since = current_time - timestamp
            days_since = time_since.days
            return days_since

    async def get_username(self, con, guild_id, user_id):
        """Helper method to get username from database for users no longer in the guild"""
        try:
            async with con.execute('SELECT username FROM archive_data WHERE server_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1', 
                                (guild_id, user_id)) as cur:
                result = await cur.fetchone()
                return result[0] if result else f"Unknown User ({user_id})"
        except Exception as e:
            print(f"Error fetching username: {e}")
            return f"Unknown User ({user_id})"

    async def fetch_messages(self, con, query, params):
        """Fetch messages with error handling"""
        try:
            async with con.execute(query, params) as cur:
                return await cur.fetchall()
        except Exception as e:
            print(f"Database error: {e}")
            return []

    async def process_messages(self, messages):
        """Process messages into a grouped structure with word counts"""
        grouped = defaultdict(lambda: {'id': None, 'words': [], 'word_counts': Counter()})
        
        for id, value in messages:
            if not value:  # Skip NULL messages
                continue
            grouped[id]['id'] = id
            words = value.lower().split()
            grouped[id]['words'].extend(words)
            grouped[id]['word_counts'].update(words)
        
        return grouped

    async def create_top_words_embed(self, title, top_words, counts, color, days):
        """Create an embed for displaying top words"""
        num_words = min(NUM_OF_RANKED_WORDS, len(top_words))
        embed = discord.Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))
        
        if num_words == 0:
            embed.description = "No words found in the messages."
            return embed
        
        embed.add_field(name="Rank", value='\n'.join(f"> #{i+1}" for i in range(num_words)), inline=True)
        embed.add_field(name="Word", value='\n'.join(f"> {word[:30]}" for word in top_words[:num_words]), inline=True)
        embed.add_field(name="Occurrence", value='\n'.join(f"> {counts[word]}" for word in top_words[:num_words]), inline=True)
        embed.set_footer(text=f'Wordcount record {days} days old. {BOTVERSION}')
        
        return embed

    async def create_word_usage_embed(self, title, user_values, user_counts, color, days):
        """Create an embed for displaying users who used a specific word"""
        num_users = len(user_values)
        embed = discord.Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))
        
        if num_users == 0:
            embed.description = "No users found who used this word."
            return embed
        
        embed.add_field(name="Rank", value='\n'.join(f"> #{i+1}" for i in range(num_users)), inline=True)
        embed.add_field(name="User", value='\n'.join(user_values), inline=True)
        embed.add_field(name="Occurrence", value='\n'.join(f"> {count}" for count in user_counts), inline=True)
        embed.set_footer(text=f'Wordcount record {days} days old. {BOTVERSION}')
        
        return embed

    def mpv_screenshot(self, stream):
        player = mpv.MPV(screenshot_format='jpeg', vo='null', hwdec='yes', screenshot_sw='yes')
        player.play(stream)
        player.wait_until_playing()
        screenshot = player.screenshot_raw()
        player.terminate()
        return screenshot
    
    def mpv_screenshots(self, streams):
        streams_matrix = BytesIO()
        count = len(streams)
        srw = math.ceil(math.sqrt(count))
        result_image = Image.new('RGB', (IMAGE_SIZE[0] * srw, IMAGE_SIZE[1] * (srw-1)))
        
        with Pool(cpu_count()//2) as pool:
            screenshots = pool.map(self.mpv_screenshot, streams)
        
        for i, screenshot in enumerate(screenshots):
            screenshot.thumbnail(IMAGE_SIZE, Image.Resampling.LANCZOS)
            result_image.paste(screenshot, (IMAGE_SIZE[0] * (i % srw), IMAGE_SIZE[1] * (i // srw)))
            result_image.save(streams_matrix, format='JPeG', quality=100)
            streams_matrix.seek(0)
        
        return streams_matrix
    
    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print('fun module online')
    
    @commands.Cog.listener()
    async def on_message(self, ctx): 
        if ctx.author.bot:
            return
        # if ctx.content.startswith('Kirk') or ctx.content.startswith('kirk') or ctx.content.startswith('KIRK'):
        #     lines = loadLines()
        #     await ctx.channel.send(random.choice(lines))
        
        userID = ctx.author.id
        channelID = ctx.channel.id
        
        # print (f'{ctx.created_at}')
        
        with open(FLAGPATH, 'r') as flagins:
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
                            
                            with open(FLAGPATH, 'r') as flagin:
                                flagdata = json.load(flagin)  
                            
                            for idx, flags in enumerate(flagdata['flags']):
                                if flags["memberID"] == userID:
                                    del flagdata['flags'][idx]
                                    break
                            
                            with open(FLAGPATH, 'w') as flagout:
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
    
    @commands.command(name='ping')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        '''Get the bot's current response time.'''
        async with ctx.typing():
            before = time.monotonic()
            before_ws = int(round(self.bot.latency * 1000, 1))
            message = await ctx.send("🏓 Pong")
            ping = (time.monotonic() - before) * 1000
            # await ctx.send(f'plong {round(self.bot.latency * 1000)} ms')
            await message.edit(content=f"🏓 WS: {before_ws}ms  |  REST: {int(ping)}ms")
    
    @commands.command(name='8ball')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _8ball(self, ctx, *, question: str):
        '''Ask the magic 8ball a question and get an answer back.'''
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
        '''
        Generate a random 9-digit number and check if it contains any repeating digits. 
        '''
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
            embedVar = discord.Embed(color=colour, timestamp=datetime.now(timezone.utc))
            embedVar.add_field(name=number, value=valuefield1, inline=False)
            embedVar.set_footer(text=BOTVERSION)
            await ctx.send(embed=embedVar)

    @commands.command(name='bigletter', aliases=['em'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def bigletter(self, ctx, *, input:str):
        '''
        Convert the given input text to a string of emojis representing each letter or number.
        '''
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
        '''
        Convert the given input text to a string of Braille characters and send it as a message to the channel. 
        '''
        async with ctx.typing():
            braille = input.lower().replace("a", "⠁").replace("b", "⠃").replace("c", "⠉").replace("d", "⠙").replace("e", "⠑").replace("f", "⠋").replace("g", "⠛").replace("h", "⠓").replace("i", "⠊").replace("j", "⠚").replace("k", "⠅").replace("l", "⠅").replace("m", "⠍").replace("n", "⠝").replace("o", "⠕").replace("p", "⠏").replace("q", "⠟").replace("r", "⠗").replace("s", "⠎").replace("t", "⠞").replace("u", "⠥").replace("v", "⠧").replace("w", "⠺").replace("x", "⠭").replace("y", "⠽").replace("z", "⠵")
            await ctx.send(f'For the blind: {braille}')
    
    @commands.command(name='youtube', aliases=['yt'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def youtube(self, ctx, *, search:str):
        '''
        Search for a YouTube video using the given search query and send a message with the first result. 
        The message includes reaction buttons for navigating through the search results. 
        '''
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
        '''
        Get the current status of the GCP Dot and send it as a message to the channel. 
        The message includes an image of the current GCP Dot and the whole chart, as well as an explanation of the dot's color and percentage. 
        '''
        async with ctx.typing():
            byteiogcpdot = BytesIO()
            options = webdriver.ChromeOptions()
            
            options.add_argument("--headless")
            options.add_argument("--window-size=1500,750")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get("https://gcpdot.com/gcpchart.php")
            time.sleep(GCP_DELAY)
            
            chart_screenshot_base64 = driver.get_screenshot_as_base64()
            chart_file = BytesIO(base64.b64decode(chart_screenshot_base64))
            
            try:
                chart_height = float(driver.find_element(By.ID, 'gcpChart').get_attribute("height"))
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
            embed = discord.Embed(title=f'Currently the GCP Dot is {colorname} at {gcppercent}%.', description=gcpStatus, color=colorint, timestamp=datetime.now(timezone.utc))
            embed.set_image(url='attachment://wholechart.png')
            embed.set_thumbnail(url='attachment://gcpdot.png')
            embed.set_footer(text=f'Use {COMMAND_PREFIX}gcp full for an explanation of all the colours. {BOTVERSION}')
            await ctx.reply(embed=embed, files=pics)
    
    @gcp_dot_base.command(name='full')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def gcp_dot_full(self, ctx):
        '''
        Get the current status of the GCP Dot and send it as a message to the channel. 
        The message includes an image of the current GCP Dot and the whole chart, as well as an explanation of the dot's color and percentage.
        The message also includes an explanation of all the colors.
        '''
        async with ctx.typing():
            byteiogcpdot = BytesIO()
            options = webdriver.ChromeOptions()
            
            options.add_argument("--headless")
            options.add_argument("--window-size=1500,750")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get("https://gcpdot.com/gcpchart.php")
            time.sleep(GCP_DELAY)
            
            chart_screenshot_base64 = driver.get_screenshot_as_base64()
            chart_file = BytesIO(base64.b64decode(chart_screenshot_base64))
            
            try:
                chart_height = float(driver.find_element(By.ID, 'gcpChart').get_attribute("height"))
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
            embed = discord.Embed(title=f'Currently the GCP Dot is {colorname} at {gcppercent}%.', description=gcpStatus, color=colorint, timestamp=datetime.now(timezone.utc))
            embed.set_image(url='attachment://wholechart.png')
            embed.set_thumbnail(url='attachment://gcpdot.png')
            embed.add_field(name="Blue ", value='Significantly small network variance. Suggestive of deeply shared, internally motivated group focus. The index is above 95%', inline=True)
            embed.add_field(name="Teal ", value='Small network variance. Probably chance fluctuation. The index is between 90% and 95%', inline=True)
            embed.add_field(name="Green ", value='Normally random network variance. This is average or expected behavior. The index is between 40% and 90%', inline=True)
            embed.add_field(name="Yellow ", value='Slightly increased network variance. Probably chance fluctuation. The index is between 10% and 40%', inline=True)
            embed.add_field(name="Orange ", value='Strongly increased network variance. May be chance fluctuation, with the index between 5% and 10%', inline=True)
            embed.add_field(name="Red ", value='Significantly large network variance. Suggests broadly shared coherence of thought and emotion. The index is less than 5%', inline=True)
            embed.set_footer(text=BOTVERSION)
            await ctx.reply(embed=embed, files=pics)        
    
    @commands.has_permissions(administrator=True)
    @commands.command(name='whocare')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def who_care(self, ctx):
        '''
        Add the who care(s) react to the message it reacted to.
        '''
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
    @commands.command(name='probe', aliases=["p"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def probe(self, ctx):
        '''
        Add the probe react to the message it reacted to.
        '''
        await ctx.message.delete()
        if ctx.message.reference:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await message.add_reaction('✝')
            await message.remove_reaction('✝', self.bot.user)
    
    @commands.has_permissions(administrator=True)
    @commands.group(name='flag', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flag_base(self, ctx, member:discord.Member, emoji:str):
        '''
        Add a flag to a member. 
        The command takes a member and an emoji as arguments and adds the emoji as a reaction to the messages send by the member.
        '''
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
                with open(FLAGPATH, 'r') as flagin:
                    flagdata = json.load(flagin)
                
                member_flag = {"memberID":member.id, "emoji":emoji}
                for flags in flagdata['flags']:
                    if flags["memberID"] == member.id:
                        flags["emoji"] = emoji
                        break
                else:
                    flagdata["flags"].append(member_flag)
                
                with open(FLAGPATH, 'w') as flagout:
                    json.dump(flagdata, flagout, indent=4)
                
                response = await ctx.reply(f'Flag added! {emoji} will now appear under every messsage send by {member.display_name}')
            else:
                response = await ctx.reply(f'{emoji} not recognized as an emoji!')
        await response.delete(delay=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.has_permissions(administrator=True)
    @flag_base.command(name='remove')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flag_remove(self, ctx, member:discord.Member):
        '''
        remove a flag from a member.
        '''
        with open(FLAGPATH, 'r') as flagin:
            flagdata = json.load(flagin)  
        
        async with ctx.typing():
            for idx, flags in enumerate(flagdata['flags']):
                if flags["memberID"] == member.id:
                    del flagdata['flags'][idx]
                    response = await ctx.reply(f'Removed flag from {member.display_name}')
                    break
            else:
                response = await ctx.reply(f'{member.display_name} has no flag!')
        
        with open(FLAGPATH, 'w') as flagout:
            json.dump(flagdata, flagout, indent=4)        
        await response.delete(delay=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.has_permissions(administrator=True)
    @flag_base.command(name='toggle')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flag_toggle(self, ctx):
        '''
        Toggle the flag react on or off in certain channels.
        '''
        with open(FLAGPATH, 'r') as flagin:
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
        
        with open(FLAGPATH, 'w') as flagout:
            json.dump(flagdata, flagout, indent=4)        
        await response.delete(delay=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.has_permissions(administrator=True)
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def emojis(self, ctx):
        '''
        Save all emojis bot can access.
        '''
        # await ctx.message.reply(f'Copy of all emojis in the server:\n{" ".join([str(emoji) for emoji in ctx.guild.emojis])}\n\nCopy of all emojis bot can access:\n{" ".join([str(emoji) for emoji in self.bot.emojis])}\n\nAll emojis saved.')
        await ctx.send('Tried to save all emojis bot can access')
        for emoji in self.bot.emojis:
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            await emoji.save(rf'{EMOJIPATH}{emoji.name}_{now}.png')    
    
    @commands.group(name='wordcount', aliases=["wc"], invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wordcount_base(self, ctx, member:Union[discord.Member, int], input_word:str=None):
        '''
        Get the word count statistics for a user in the server. 
        The command takes a member and an optional input word as arguments and returns the top used words and their occurrence count for the user.
        '''
        if isinstance(member, discord.Member):
            user_id = member.id
        else:
            user_id = member
        
        if input_word is not None:
            input_word = input_word.lower()
        
        try:
            async with aiosqlite.connect(ARCHIVE_DATABASE) as con:
                # Fetch messages
                messages = await self.fetch_messages(con, 
                    'SELECT user_id, message FROM archive_data WHERE server_id = ?', 
                    (ctx.guild.id,))
                
                # Process into grouped structure
                grouped = await self.process_messages(messages)
                
                if user_id not in grouped:
                    await ctx.send(f"{member} has no recorded messages")
                    return
                
                data = grouped[user_id]
                
                # Get display name
                try:
                    member_obj = ctx.guild.get_member(user_id)
                    display_name = member_obj.display_name if member_obj else None
                    if not display_name:
                        display_name = await self.get_username(con, ctx.guild.id, user_id)
                except Exception:
                    try:
                        display_name = await self.get_username(con, ctx.guild.id, user_id)
                    except Exception as e:
                        msg = await ctx.reply(f'Error retrieving user info: {e}')
                        await ctx.message.delete(delay=MSG_DEL_DELAY)
                        await msg.delete(delay=MSG_DEL_DELAY)
                        return
                
                days = await self.daysago()
                
                # Generate appropriate embed based on input
                if input_word is None:
                    # Get top words for user
                    top_words = [word for word, count in data['word_counts'].most_common(NUM_OF_RANKED_WORDS)]
                    embed = await self.create_top_words_embed(
                        title=f"Top {NUM_OF_RANKED_WORDS} used words for {display_name} in {ctx.guild.name}",
                        top_words=top_words,
                        counts=data['word_counts'],
                        color=0x00ff00,
                        days=days)
                else:
                    # Get specific word usage for user
                    count = data['word_counts'].get(input_word, 0)
                    embed = discord.Embed(
                        title=f"{display_name}'s use of '{input_word[:128]}' in {ctx.guild.name}", 
                        color=0x00ff00, 
                        timestamp=datetime.now(timezone.utc))
                    embed.add_field(name=f"Occurrences of {input_word}", value=f"{count}", inline=False)
                    embed.set_footer(text=f'Wordcount record {days} days old. {BOTVERSION}')
                
                await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @wordcount_base.error
    async def wordcount_base_error(self, ctx, error):
        '''
        Error handler for wordcount_base command.
        '''
        if isinstance(error, commands.UserInputError):
            msg = await ctx.reply('The second argument needs to be either: [`@user` or `ID`]'+f', `server`, or `channel`. Refer to `{COMMAND_PREFIX}help fun wordcount` for details on all the possible commands.')
            ctx._ignore_ = True
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @wordcount_base.command(name='server')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wordcount_server(self, ctx, input_word:str=None):
        '''
        Get the word count statistics for the server. 
        The command takes an optional input word as an argument and returns the top used words and their occurrence count for the server.
        '''
        if input_word is not None:
            input_word = input_word.lower()
        
        try:
            async with aiosqlite.connect(ARCHIVE_DATABASE) as con:
                # Fetch messages
                messages = await self.fetch_messages(con, 
                    'SELECT user_id, message FROM archive_data WHERE server_id = ?', 
                    (ctx.guild.id,))
                
                # Process into grouped structure
                grouped = await self.process_messages(messages)
                
                if not grouped:
                    await ctx.send(f"No messages found for {ctx.guild.name}")
                    return
                
                days = await self.daysago()
                
                if input_word is None:
                    # Calculate total word counts across all users
                    total_counts = Counter()
                    for user_data in grouped.values():
                        total_counts.update(user_data['word_counts'])
                    
                    # Get top words for server
                    top_words = [word for word, count in total_counts.most_common(NUM_OF_RANKED_WORDS)]
                    embed = await self.create_top_words_embed(
                        title=f"Top {NUM_OF_RANKED_WORDS} used words in {ctx.guild.name}",
                        top_words=top_words,
                        counts=total_counts,
                        color=0xff0000,
                        days=days)
                else:
                    # Find users who used the specific word
                    user_word_counts = {}
                    for user_id, user_data in grouped.items():
                        count = user_data['word_counts'].get(input_word, 0)
                        if count > 0:
                            user_word_counts[user_id] = count
                    
                    if not user_word_counts:
                        await ctx.send(f"No user in {ctx.guild.name} used the word '{input_word}'.")
                        return
                    
                    # Sort users by count
                    sorted_users = sorted(user_word_counts.items(), key=lambda x: x[1], reverse=True)
                    num_users = min(NUM_OF_RANKED_WORDS, len(sorted_users))
                    
                    # Get usernames for display
                    user_values = []
                    user_counts = []
                    
                    for user_id, count in sorted_users[:num_users]:
                        member = ctx.guild.get_member(user_id)
                        if member:
                            user_values.append(f"> {member.display_name}")
                        else:
                            username = await self.get_username(con, ctx.guild.id, user_id)
                            user_values.append(f"> {username}")
                        user_counts.append(str(count))
                    
                    embed = await self.create_word_usage_embed(
                        title=f"Top {num_users} users who used '{input_word[:128]}' in {ctx.guild.name}",
                        user_values=user_values,
                        user_counts=user_counts,
                        color=0xff0000,
                        days=days)
                
                await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @wordcount_base.command(name='channel')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wordcount_channel(self, ctx, input_word:str=None):
        '''
        Get the word count statistics for the channel. 
        The command takes an optional input word as an argument and returns the top used words and their occurrence count for the channel.
        '''
        if input_word is not None:
            input_word = input_word.lower()
        
        try:
            async with aiosqlite.connect(ARCHIVE_DATABASE) as con:
                # Fetch messages for this channel only
                messages = await self.fetch_messages(con, 
                    'SELECT user_id, message FROM archive_data WHERE channel_id = ?', 
                    (ctx.channel.id,))
                
                # Process into grouped structure
                grouped = await self.process_messages(messages)
                
                if not grouped:
                    await ctx.send(f"No messages found for {ctx.channel.name}")
                    return
                
                days = await self.daysago()
                
                if input_word is None:
                    # Calculate total word counts across all users in this channel
                    total_counts = Counter()
                    for user_data in grouped.values():
                        total_counts.update(user_data['word_counts'])
                    
                    # Get top words for channel
                    top_words = [word for word, count in total_counts.most_common(NUM_OF_RANKED_WORDS)]
                    embed = await self.create_top_words_embed(
                        title=f"Top {NUM_OF_RANKED_WORDS} used words in {ctx.channel.name}",
                        top_words=top_words,
                        counts=total_counts,
                        color=0x0000ff,
                        days=days)
                else:
                    # Find users who used the specific word in this channel
                    user_word_counts = {}
                    for user_id, user_data in grouped.items():
                        count = user_data['word_counts'].get(input_word, 0)
                        if count > 0:
                            user_word_counts[user_id] = count
                    
                    if not user_word_counts:
                        await ctx.send(f"No user in {ctx.channel.name} used the word '{input_word}'.")
                        return
                    
                    # Sort users by count
                    sorted_users = sorted(user_word_counts.items(), key=lambda x: x[1], reverse=True)
                    num_users = min(NUM_OF_RANKED_WORDS, len(sorted_users))
                    
                    # Get usernames for display
                    user_values = []
                    user_counts = []
                    
                    for user_id, count in sorted_users[:num_users]:
                        member = ctx.guild.get_member(user_id)
                        if member:
                            user_values.append(f"> {member.display_name}")
                        else:
                            username = await self.get_username(con, ctx.guild.id, user_id)
                            user_values.append(f"> {username}")
                        user_counts.append(str(count))
                    
                    embed = await self.create_word_usage_embed(
                        title=f"Top {num_users} users who used '{input_word[:128]}' in {ctx.channel.name}",
                        user_values=user_values,
                        user_counts=user_counts,
                        color=0x0000ff,
                        days=days)
                
                await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Fun(bot))