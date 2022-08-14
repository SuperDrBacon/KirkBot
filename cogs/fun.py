import json
import discord
import random
import time
import typing
import asyncio
import os
import re
import urllib.parse, urllib.request, re
from io import BytesIO
from discord_ui import Button
from discord.ext import commands
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import InvalidSessionIdException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from numpy import interp
from PIL import Image, ImageDraw, ImageColor

ospath = os.path.abspath(os.getcwd())
path = rf'{ospath}/cogs/kirklines.txt'
tagpath = rf'{ospath}/cogs/tag.json'
imagepath = rf'{ospath}/images/'
flagpath = rf'{ospath}/cogs/flags.json'
high = 0
delay = 1
msgdeldelay = 3
byteiogcpdot = BytesIO()
byteiogchart = BytesIO()

with open(path, 'r') as f:
    lines = [line.rstrip() for line in f]

class fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print('fun module online')
    
    
    @commands.Cog.listener()
    async def on_message(self, ctx): 
        if ctx.author.bot:
            return
        if ctx.content.startswith('Kirk') or ctx.content.startswith('kirk') or ctx.content.startswith('KIRK'):
            await ctx.channel.send(random.choice(lines))
        
        userID = ctx.author.id
        with open(flagpath, 'r') as flagins:
            flagdata = json.load(flagins)
        try:
            for flags in flagdata['flags']:
                if userID == flags["memberId"]:
                    await ctx.add_reaction(flags["emoji"])
                    raise StopIteration
        except StopIteration:
            pass


    @commands.command()
    async def ping(self, ctx):
        '''See delay of the bot'''
        before = time.monotonic()
        before_ws = int(round(self.bot.latency * 1000, 1))
        message = await ctx.send("🏓 Pong")
        ping = (time.monotonic() - before) * 1000
        # await ctx.send(f'plong {round(self.bot.latency * 1000)} ms')
        await message.edit(content=f"🏓 WS: {before_ws}ms  |  REST: {int(ping)}ms")
    
    @commands.command(aliases=['8ball'])
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
        await ctx.send(f'question: {question}\n Answer: {random.choice(responses)}')
    
    @commands.command(name='checkem', aliases=['check', 'c'])
    async def checkem(self, ctx):
        '''[checkem] [check] [c]. Check random number for dubs trips etc.'''
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
    async def bigletter(self, ctx, *, input:str):
        '''[bigletter] [em]. Types you messages in letter emojis. '''
        await ctx.message.delete()
        emojis = []
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
    async def braille(self, ctx, *, input:str):
        '''[braille] [br]. Converts you message to braille so blind people can read it.'''
        braille = input.lower().replace("a", "⠁").replace("b", "⠃").replace("c", "⠉").replace("d", "⠙").replace("e", "⠑").replace("f", "⠋").replace("g", "⠛").replace("h", "⠓").replace("i", "⠊").replace("j", "⠚").replace("k", "⠅").replace("l", "⠅").replace("m", "⠍").replace("n", "⠝").replace("o", "⠕").replace("p", "⠏").replace("q", "⠟").replace("r", "⠗").replace("s", "⠎").replace("t", "⠞").replace("u", "⠥").replace("v", "⠧").replace("w", "⠺").replace("x", "⠭").replace("y", "⠽").replace("z", "⠵")
        await ctx.send(f'For the blind: {braille}')
    
    @commands.command(name='youtube', aliases=['yt'])
    async def youtube(self, ctx, *, search:str):
        '''[youtube] [yt]. Posts youtube vid from search.'''
        query_string = urllib.parse.urlencode({'search_query':search})
        html_content = urllib.request.urlopen('https://www.youtube.com/results?' + query_string)
        search_results = re.findall(r"watch\?v=(\S{11})", html_content.read().decode())
        await ctx.send('https://www.youtube.com/watch?v=' + search_results[0])
    
    @commands.group(name='gcp', invoke_without_command=True)
    async def gcp_dot_base(self, ctx):
        options = webdriver.ChromeOptions()
        options.headless = True
        driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver', options=options)
        driver.set_window_size(1000,500)
        driver.get("https://gcpdot.com/gcpchart.php")
        time.sleep(delay)
        driver.find_element(By.TAG_NAME, 'body').screenshot(f'{imagepath}wholechart.png')
        
        try:
            chart_height = float(driver.find_element(By.ID, 'gcpChartShadow').get_attribute("height")) + 20
            dot = driver.find_elements(By.XPATH, '/html/body/div/div')[-1]
            dot_id = dot.get_attribute('id')
            dot_height = driver.find_element(By.ID, dot_id).value_of_css_property('top')
            dot_height = float(dot_height.replace('px', ''))
            
            # Map dot height into domain [0.0...1.0] rather than raw css property value
            high = interp(float(dot_height), [0, chart_height], [0.0, 1.0])
            
            if (high == 0):
                color = '#505050'
            elif (high < 0.01):
                color = '#FFA8C0'
            elif (high >= 0.0 and high < 0.05):
                color = '#FF1E1E'
            elif (high >= 0.05 and high < 0.08):
                color = '#FFB82E'
            elif (high >= 0.08 and high < 0.15):
                color = '#FFD517'
            elif (high >= 0.15 and high < 0.23):
                color = '#FFFA40'
            elif (high >= 0.23 and high < 0.30):
                color = '#F9FA00'
            elif (high >= 0.30 and high < 0.40):
                color = '#AEFA00'
            elif (high >= 0.40 and high < 0.90):
                color = '#64FA64'
            elif (high >= 0.90 and high < 0.9125):
                color = '#64FAAB'
            elif (high >= 0.9125 and high < 0.93):
                color = '#ACF2FF'
            elif (high >= 0.93 and high < 0.96):
                color = '#0EEEFF'
            elif (high >= 0.96 and high < 0.98):
                color = '#24CBFD'
            elif (high >= 0.98 and high < 1.00):
                color = '#5655CA'
            else:
                color = '#505050'
            
            if (high == 0):
                gcpStatus = 'It is hivemind time!'
                colorname = 'grey'
            elif (high < 0.05):
                gcpStatus = 'Significantly large network variance. Suggests broadly shared coherence of thought and emotion. The index is less than 5%'
                colorname = 'red'
            elif (high >= 0.05 and high < 0.10):
                gcpStatus = 'Strongly increased network variance. May be chance fluctuation, with the index between 5% and 10%'
                colorname = 'orange'
            elif (high >= 0.10 and high < 0.40):
                gcpStatus = 'Slightly increased network variance. Probably chance fluctuation. The index is between 10% and 40%'
                colorname = 'yellow'
            elif (high >= 0.40 and high < 0.90):
                gcpStatus = 'Normally random network variance. This is average or expected behavior. The index is between 40% and 90%'
                colorname = 'green'
            elif (high >= 0.90 and high < 0.95):
                gcpStatus = 'Small network variance. Probably chance fluctuation. The index is between 90% and 95%'
                colorname = 'teal'
            elif (high >= 0.95 and high < 1.0):
                gcpStatus = 'Significantly small network variance. Suggestive of deeply shared, internally motivated group focus. The index is above 95%'
                colorname = 'blue'
            else:
                color = 'grey'
                gcpStatus = 'The Dot is broken!'
        
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
        
        # wholechartfile = discord.File(f'{imagepath}wholechart.png', filename='wholechart.png')
        # dotfile = discord.File(byteiogcpdot, filename='gcpdot.png')
        
        pics = [discord.File(byteiogcpdot, filename='gcpdot.png'), discord.File(f'{imagepath}wholechart.png', filename='wholechart.png')]
        colorint = int(color[1:], 16)
        gcppercent = round(high * 100, 2)
        embed = discord.Embed(title=f'Currently the GCP Dot is {colorname} at {gcppercent}%.', description=gcpStatus, color=colorint, inline=True)
        embed.set_image(url='attachment://wholechart.png')
        embed.set_thumbnail(url='attachment://gcpdot.png')
        embed.set_footer(text='Use .,gcp full for an explanation of all the colours.')
        await ctx.reply(embed=embed, files=pics)
    
    @gcp_dot_base.command(name='full', invoke_without_command=True)
    async def gcp_dot_full(self, ctx):
        options = webdriver.ChromeOptions()
        options.headless = True
        driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver', options=options)
        driver.set_window_size(1000,500)
        driver.get("https://gcpdot.com/gcpchart.php")
        time.sleep(delay)
        driver.find_element(By.TAG_NAME, 'body').screenshot(f'{imagepath}wholechart.png')
        
        try:
            chart_height = float(driver.find_element(By.ID, 'gcpChartShadow').get_attribute("height")) + 20
            dot = driver.find_elements(By.XPATH, '/html/body/div/div')[-1]
            dot_id = dot.get_attribute('id')
            dot_height = driver.find_element(By.ID, dot_id).value_of_css_property('top')
            dot_height = float(dot_height.replace('px', ''))
            
            # Map dot height into domain [0.0...1.0] rather than raw css property value
            high = interp(float(dot_height), [0, chart_height], [0.0, 1.0])
            
            if (high == 0):
                color = '#505050'
            elif (high < 0.01):
                color = '#FFA8C0'
            elif (high >= 0.0 and high < 0.05):
                color = '#FF1E1E'
            elif (high >= 0.05 and high < 0.08):
                color = '#FFB82E'
            elif (high >= 0.08 and high < 0.15):
                color = '#FFD517'
            elif (high >= 0.15 and high < 0.23):
                color = '#FFFA40'
            elif (high >= 0.23 and high < 0.30):
                color = '#F9FA00'
            elif (high >= 0.30 and high < 0.40):
                color = '#AEFA00'
            elif (high >= 0.40 and high < 0.90):
                color = '#64FA64'
            elif (high >= 0.90 and high < 0.9125):
                color = '#64FAAB'
            elif (high >= 0.9125 and high < 0.93):
                color = '#ACF2FF'
            elif (high >= 0.93 and high < 0.96):
                color = '#0EEEFF'
            elif (high >= 0.96 and high < 0.98):
                color = '#24CBFD'
            elif (high >= 0.98 and high < 1.00):
                color = '#5655CA'
            else:
                color = '#505050'
            
            if (high == 0):
                gcpStatus = 'It is hivemind time!'
                colorname = 'grey'
            elif (high < 0.05):
                gcpStatus = 'Significantly large network variance. Suggests broadly shared coherence of thought and emotion. The index is less than 5%'
                colorname = 'red'
            elif (high >= 0.05 and high < 0.10):
                gcpStatus = 'Strongly increased network variance. May be chance fluctuation, with the index between 5% and 10%'
                colorname = 'orange'
            elif (high >= 0.10 and high < 0.40):
                gcpStatus = 'Slightly increased network variance. Probably chance fluctuation. The index is between 10% and 40%'
                colorname = 'yellow'
            elif (high >= 0.40 and high < 0.90):
                gcpStatus = 'Normally random network variance. This is average or expected behavior. The index is between 40% and 90%'
                colorname = 'green'
            elif (high >= 0.90 and high < 0.95):
                gcpStatus = 'Small network variance. Probably chance fluctuation. The index is between 90% and 95%'
                colorname = 'teal'
            elif (high >= 0.95 and high < 1.0):
                gcpStatus = 'Significantly small network variance. Suggestive of deeply shared, internally motivated group focus. The index is above 95%'
                colorname = 'blue'
            else:
                color = 'grey'
                gcpStatus = 'The Dot is broken!'
        
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
        
        # wholechartfile = discord.File(f'{imagepath}wholechart.png', filename='wholechart.png')
        # dotfile = discord.File(byteiogcpdot, filename='gcpdot.png')
        
        pics = [discord.File(byteiogcpdot, filename='gcpdot.png'), discord.File(f'{imagepath}wholechart.png', filename='wholechart.png')]
        colorint = int(color[1:], 16)
        gcppercent = round(high * 100, 2)
        embed = discord.Embed(title=f'Currently the GCP Dot is {colorname} at {gcppercent}%.', description=gcpStatus, color=colorint, inline=True)
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
    async def tag_get(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name='Tag')
        guild = self.bot.get_guild(ctx.guild.id)
        for members in guild.members:
            if role in members.roles:
                await ctx.channel.send(f'{members.mention} is tagged!')
    
    @commands.command(name='whocare', aliases=["wc"])
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
    @commands.group(name='flag', invoke_without_command=True)
    async def flag_base(self, ctx, member:discord.Member, emoji:str):
        re_emoji_custom = r'<a?:.+?:\d{19}>'
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
        
        if (re.match(re_emoji_custom, emoji)) or (re.match(re_emoji_generic, emoji)):
            with open(flagpath, 'r') as flagin:
                flagdata = json.load(flagin)
            
            member_flag = {"memberId":member.id, "emoji":emoji}
            try:
                for flags in flagdata['flags']:
                    if member.id == flags["memberId"]:
                        flags["emoji"] = emoji
                        raise StopIteration
                flagdata["flags"].append(member_flag)
            except StopIteration:
                pass
            
            with open(flagpath, 'w') as flagout:
                json.dump(flagdata, flagout, indent=4)
            
            response = await ctx.reply(f'Flag added! {emoji} will now appear under every messsage send by {member.display_name}')
        else:
            response = await ctx.reply(f'{emoji} not recognized as an emoji!')
        await response.delete(delay=msgdeldelay)
        await ctx.message.delete(delay=msgdeldelay)
    
    @flag_base.command(name='remove', invoke_without_command=True)
    async def flag_remove(self, ctx, member:discord.Member):
        with open(flagpath, 'r') as flagin:
            flagdata = json.load(flagin)  
        
        try:
            for idx, flags in enumerate(flagdata['flags']):
                if flags["memberId"] == member.id:
                    del flagdata['flags'][idx]
                    response = await ctx.reply(f'Removed flag from {member.display_name}')
        except Exception:
            response = await ctx.reply(f'{member.display_name} has no flag!')
        
        with open(flagpath, 'w') as flagout:
            json.dump(flagdata, flagout, indent=4)        
        await response.delete(delay=msgdeldelay)
        await ctx.message.delete(delay=msgdeldelay)


    @tag_base.error
    async def tag_base_handeler(self, ctx, error):
        if (discord.utils.get(ctx.guild.roles, name='Tag')) is None:
            await ctx.guild.create_role(name='Tag')
            await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, name='Tag'))
            
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply('To tag use .,tag @user')

def setup(bot):
    bot.add_cog(fun(bot))