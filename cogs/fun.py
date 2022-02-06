import discord
import random
import time
import typing
import asyncio
import os
import urllib.parse, urllib.request, re
import discord_components
from discord.ui import Button, View

from discord.ext import commands
# from discord.ext.commands.context import P
path = os.path.abspath(os.getcwd())

with open(path + '/cogs/kirklines.txt', 'r') as f:
    # lines = f.readline().rstrip()
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
        if (ctx.author.bot):
            return
        if ctx.content.startswith('Kirk'):
            await ctx.channel.send(random.choice(lines))
            # await ctx.channel.send('ssdf')
        # else:
        #     await ctx.channel.send('ghjg')
        #     await ctx.send('dik')
        #     return
        
        
        # await self.client.process_commands(ctx)        
        # await discord.process_commands(self, ctx)
        # await self.process_commands(self, ctx)
        # ctx.process_commands(self)
        # await ctx.process_message()

    #commands
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
    async def _8ball(self, ctx, *, question):
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
    async def bigletter(self, ctx, *, input):
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
    async def braille(self, ctx, *, input):
        '''[braille] [br]. Converts you message to braille so blind people can read it.'''
        braille = input.lower().replace("a", "⠁").replace("b", "⠃").replace("c", "⠉").replace("d", "⠙").replace("e", "⠑").replace("f", "⠋").replace("g", "⠛").replace("h", "⠓").replace("i", "⠊").replace("j", "⠚").replace("k", "⠅").replace("l", "⠅").replace("m", "⠍").replace("n", "⠝").replace("o", "⠕").replace("p", "⠏").replace("q", "⠟").replace("r", "⠗").replace("s", "⠎").replace("t", "⠞").replace("u", "⠥").replace("v", "⠧").replace("w", "⠺").replace("x", "⠭").replace("y", "⠽").replace("z", "⠵")
        await ctx.send(f'For the blind: {braille}')
    
    @commands.command(name='youtube', aliases=['yt'])
    async def youtube(self, ctx, *, search):
        '''[youtube] [yt]. Posts youtube vid from search.'''
        query_string = urllib.parse.urlencode({
            'search_query':search
        })
        html_content = urllib.request.urlopen(
            'https://www.youtube.com/results?' + query_string
        )
        search_results = re.findall(r"watch\?v=(\S{11})", html_content.read().decode())
        await ctx.send('https://www.youtube.com/watch?v=' + search_results[0])
    
    
    # @commands.command(name='button_delete', aliases=['but'])
    # async def button(self, ctx):
    #     button = Button(label='dick', style=discord.ButtonStyle.red, emoji='<:pog_KamiChamp:852026330761789440>')
    #     view = View()
    #     view.add_item(button)
    #     await ctx.send('sdf')
    #     await ctx.send(view=view)
    
    
    # @commands.command(name='dropdown', aliases=['menu'])
    # async def dropdown(self, ctx):
    #     await ctx.send('5')
    #     view = DropdownView()
    #     await ctx.send('0')
    #     await ctx.send(f'Pick your favourite colour:', view=view)
        

        # options = [
        #     discord.SelectOption(
        #         label="Red", description="Your favourite colour is red", emoji="🟥"
        #     ),
        #     discord.SelectOption(
        #         label="Green", description="Your favourite colour is green", emoji="🟩"
        #     ),
        #     discord.SelectOption(
        #         label="Blue", description="Your favourite colour is blue", emoji="🟦"
        #     ),
            
        # placeholder="Choose your favourite colour...",
        # min_values=1,
        # max_values=1,
        # options=options,
            
        
    
    
    
    # @commands.command()
    # @commands.command()
    # @commands.command()
    # @commands.command()


# def setup(bot):
#     bot.add_cog(fun(bot))

# class DropdownView(discord.ui.View):
#     def __init__(self):
#         super().__init__()

#         # Adds the dropdown to our view object.
#         self.add_item(Dropdown())

# class Dropdown(discord.ui.Select):
#     def __init__(self):

#         # Set the options that will be presented inside the dropdown
#         options = [
#             discord.SelectOption(
#                 label="Red", description="Your favourite colour is red", emoji="🟥"
#             ),
#             discord.SelectOption(
#                 label="Green", description="Your favourite colour is green", emoji="🟩"
#             ),
#             discord.SelectOption(
#                 label="Blue", description="Your favourite colour is blue", emoji="🟦"
#             ),
#         ]

#         # The placeholder is what will be shown when no option is chosen
#         # The min and max values indicate we can only pick one of the three options
#         # The options parameter defines the dropdown options. We defined this above
#         super().__init__(
#             placeholder="Choose your favourite colour...",
#             min_values=1,
#             max_values=1,
#             options=options,
#         )

#     async def callback(self, interaction: discord.Interaction):
#         # Use the interaction object to send a response message containing
#         # the user's favourite colour or choice. The self object refers to the
#         # Select object, and the values attribute gets a list of the user's
#         # selected options. We only want the first one.
#         await interaction.response.send_message(
#             f"Your favourite colour is {self.values[0]}"
#         )




# class MyNewHelp(commands.MinimalHelpCommand):
#    async def send_pages(self):
#        destination = self.get_destination()
#        for page in self.paginator.pages:
#            embed = discord.Embed(description=page)
#            await destination.send(embed=embed)

# try:
#     message = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel.id == ctx.channel.id, timeout=15)
# except asyncio.TimeoutError:
#     return await ctx.send("You didn't respond")
# else:
    
# try:
#     reaction, user = await bot.wait_for('reaction_add', check=lambda r, u: u == ctx.author and r.message.channel.id == ctx.channel.id, timeout=15)
# except asyncio.TimeoutError:
#     return await ctx.send("You didn't respond")
# else:
    
# import discord
# from discord.ext import commands


# class Fun(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot

    

# def setup(bot):
#     bot.add_cog(Fun(bot))

# @commands.has_permissions(el sex=True)

# class MyButton(discord.ui.Button):

#     async def callback(self, interaction: discord.Interaction):
#         return await super().callback(interaction)
    
# class MyButton(discord.ui.Button):

#     def __init__(self, *, style: ButtonStyle = ..., label: Optional[str] = None,
#                 disabled: bool = False, custom_id: Optional[str] = None,
#                 url: Optional[str] = None, emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
#                 row: Optional[int] = None, argname: _type):
#         super().__init__(style=style, label=label, disabled=disabled,
#                         custom_id=custom_id, url=url, emoji=emoji, row=row, argname=argname)

#     async def callback(self, interaction: discord.Interaction):
#         return await super().callback(interaction)

# class MySelect(discord.ui.Select):

#    async def callback(self, interaction: discord.Interaction):
# return await super().callback(interaction)

# @bot.check
# async def bot_check(ctx):
#     sadad



def setup(bot):
    bot.add_cog(fun(bot))