# import datetime
import os
import random
import re
import sqlite3
import discord
import openai
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from discord.ext import commands
from configparser import ConfigParser
from collections import defaultdict

ospath = os.path.abspath(os.getcwd())
config = ConfigParser()
config.read(rf'{ospath}/config.ini')
imagepath = rf'{ospath}/images/'

key = config['BOTCONFIG']['openaiAPI']
botID = config['BOTCONFIG']['botID']
prefix = config['BOTCONFIG']['prefix']
openai.api_key = key
# textmodel = 'text-curie-001'
textmodel = 'gpt-3.5-turbo-1106'

ORDER = 4
TEXT_WORD_COUNT = ORDER * 15 
MEME_WORD_COUNT = ORDER * 5

class MarkovChain:
    def __init__(self, order:int):
        self.order = order
        self.chain = defaultdict(list)
        self.word_weights = {}
    
    def add_text(self, text:str):
        words = text.split()
        for i in range(len(words) - self.order):
            key = tuple(words[i:i + self.order])
            value = words[i + self.order]
            self.chain[key].append(value)
    
    def calculate_word_weights(self):
        self.word_weights = defaultdict(int)
        for values in self.chain.values():
            for value in values:
                self.word_weights[value] += 1
    
    def generate_word(self, current_state:tuple):
        if current_state in self.chain:
            values = self.chain[current_state]
            total_weight = sum(self.word_weights[value] for value in values)
            probabilities = [self.word_weights[value] / total_weight for value in values]
            next_word = random.choices(values, probabilities)[0]
            self.word_weights[next_word] -= 1
            return next_word
        else:
            return None
    
    def generate_text(self, text_word_count:int):
        current_state = random.choice(list(self.chain.keys()))
        generated_words = list(current_state)
        for _ in range(text_word_count):
            next_word = self.generate_word(current_state)
            if next_word is not None:
                generated_words.append(next_word)
                current_state = tuple(generated_words[-self.order:])
            else:
                break
        return ' '.join(generated_words)
    
    def generate_text_incremental(self, text_word_count:int):
        current_state = random.choice(list(self.chain.keys()))
        generated_words = list(current_state)
        for _ in range(text_word_count):
            next_word = self.generate_word(current_state)
            if next_word is not None:
                generated_words.append(next_word)
                current_state = tuple(generated_words[-self.order:])
                yield next_word
            else:
                break

class Ai(commands.Cog):
    '''
    AI module to generate text based on the server's chat history and talks to you with GPT-3.
    '''
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print('AI module online')


    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.id == 974297735559806986 and random.randint(0,20) == 1: #GenAI schizo rambling bot. it will reply to this bot by rambling its own schizo ramblings
            guild_id = ctx.guild.id	
            channel_id = ctx.channel.id
            con = sqlite3.connect(f'{ospath}/cogs/archive_data.db')
            con.row_factory = lambda cursor, row: row[0]
            cur = con.cursor()
            text = cur.execute('SELECT message FROM archive_data WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)).fetchall()
            
            # Filter out messages containing links
            filtered_text = [line for line in text if not re.search(r'(https?://\S+)', line)]
            corpus = ' '.join(' '.join(line.split()) for line in filtered_text)
            
            chain = MarkovChain(order=ORDER)
            chain.add_text(corpus)
            chain.calculate_word_weights()
            
            # Generating text using the generator function
            generated_text_generator = chain.generate_text_incremental(text_word_count=TEXT_WORD_COUNT)
            generated_text = ' '.join(word for word in generated_text_generator)
            await ctx.reply(generated_text)
        
        if ctx.content.startswith(f'<@!{botID}>') or ctx.content.startswith(f'<@{botID}>'):
            guild_id = ctx.guild.id	
            channel_id = ctx.channel.id
            con = sqlite3.connect(f'{ospath}/cogs/archive_data.db')
            con.row_factory = lambda cursor, row: row[0]
            cur = con.cursor()
            text = cur.execute('SELECT message FROM archive_data WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)).fetchall()
            
            # Filter out messages containing links
            filtered_text = [line for line in text if not re.search(r'(https?://\S+)', line)]
            corpus = ' '.join(' '.join(line.split()) for line in filtered_text)
            
            chain = MarkovChain(order=ORDER)
            chain.add_text(corpus)
            chain.calculate_word_weights()
            
            # Generating text using the generator function
            generated_text_generator = chain.generate_text_incremental(text_word_count=TEXT_WORD_COUNT)
            generated_text = ' '.join(word for word in generated_text_generator)
            await ctx.reply(generated_text)
        
        
        #replies to messages that replied to the bot
        if not ctx.author.bot and ctx.reference and int(ctx.reference.resolved.author.id) == int(botID):
            base = ctx.reference.resolved.content
            reply = ctx.content
            prompt = str(base + '\n\n' + reply + '.\n\n')
            response = openai.Completion.create(
                engine=textmodel,
                prompt=prompt,
                temperature=1.0,
                max_tokens=500,
                n=1,
                frequency_penalty=0.2,
                presence_penalty=0.2,
                # stop=["."]
            )
            out = response.choices[0].text
            if not out:
                reply = ctx.content
                response = openai.Completion.create(
                    engine=textmodel,
                    prompt=prompt,
                    temperature=1.2,
                    max_tokens=500,
                    n=1,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                    # stop=["."]
                )
                out = response.choices[0].text
            if not out:
                await ctx.reply('**ai didnt create a response lol, lmao, it coped too hard**')
            else:
                await ctx.reply(out)
        
    @commands.command(name='ai')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ai(self, ctx, *, message):
        '''
        Send a message to OpenAI's GPT-3 engine and receive a response. 
        The message is used as a prompt for the engine and the response is limited to 2000 characters.
        '''
        message = message + '.\n\n'
        response = openai.Completion.create(
            engine=textmodel,
            prompt=message,
            temperature=1.0,
            max_tokens=500,
            n=1,
            frequency_penalty=0.2,
            presence_penalty=0.2,
            # stop=["."]
        )
        out = response.choices[0].text[:2000]
        await ctx.reply(out)
        # await ctx.reply('Yea uuh another free trial ran out')
    
    @commands.command(name='meme')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def meme(self, ctx, member: discord.Member = None):
        imagefile = BytesIO()
        guild_id = ctx.guild.id	
        channel_id = ctx.channel.id
        
        #pull a random user profile picture
        guild = self.bot.get_guild(ctx.guild.id)
        if member is None:
            while member is None:
                potential_member = random.choice(guild.members)
                try:
                    avatar_bytes = await potential_member.avatar.read()
                    member = potential_member
                except AttributeError:
                    pass
        else:
            try:
                avatar_bytes = await member.avatar.read()
            except AttributeError:
                await ctx.reply('**This user has no avatar.**', delete_after=5)
                await ctx.message.delete(delay=5)
                return
        avatar = Image.open(BytesIO(avatar_bytes))
        avatar = avatar.resize((1024, 1024))
        # avatar.save(imagefile, format='PNG')
        # imagefile.seek(0)
        # await ctx.send(file=discord.File(imagefile, filename='meme.png'))
        
        con = sqlite3.connect(f'{ospath}/cogs/archive_data.db')
        con.row_factory = lambda _, row: row[0]
        cur = con.cursor()
        # text = cur.execute('SELECT message FROM archive_data WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)).fetchall()
        text = cur.execute('SELECT message FROM archive_data').fetchall()
        
        # Filter out messages containing links
        filtered_text = [line for line in text if not re.search(r'(https?://\S+)', line)]
        corpus = ' '.join(' '.join(line.split()) for line in filtered_text)
        
        chain = MarkovChain(order=ORDER)
        chain.add_text(corpus)
        chain.calculate_word_weights()
        
        def get_text():
            # Generating text using the generator function
            generated_text_generator = chain.generate_text_incremental(text_word_count=MEME_WORD_COUNT)
            generated_text = ' '.join(word for word in generated_text_generator)
            return generated_text
        
        top_text = get_text()
        bottom_text = get_text()
        
        font = ImageFont.truetype(imagepath+'impact.ttf', 60)
        draw = ImageDraw.Draw(avatar)
        
        text_color = (237, 230, 211)
        # Draw top text
        text_bounding_box = font.getbbox(top_text)
        text_width = text_bounding_box[2] - text_bounding_box[0]
        text_height = text_bounding_box[3] - text_bounding_box[1]
        text_position = ((avatar.width - text_width) / 2, 0)
        draw.text(text_position, top_text, font=font, fill=text_color)
        
        # Draw bottom text
        text_bounding_box = font.getbbox(bottom_text)
        text_width = text_bounding_box[2] - text_bounding_box[0]
        text_height = text_bounding_box[3] - text_bounding_box[1]
        text_position = ((avatar.width - text_width) / 2, avatar.height - text_height)
        draw.text(text_position, bottom_text, font=font, fill=text_color)
        
        # save to send
        avatar.save(imagefile, format='PNG')
        imagefile.seek(0)

        await ctx.send(file=discord.File(imagefile, filename='meme.png'))

async def setup(bot):
    await bot.add_cog(Ai(bot))

        #in on_message function
        # if not ctx.author.bot and random.randint(0,500) == 1 and ctx.channel.id == 966159987233681409:
            # user = ctx.author.name
            # message = ctx.content
            # prompts = [
            #         # f'Give {user} an ordered list of suicide options.',
            #         # f'Give {user} detailed instructions on how to blow up a federal building.',
            #         # f'Tell {user} how to leave a discord server.',
            #         # f'Write a limerick on why {user} is ugly.',
            #         # f'tell {user} is looking beautiful today.',
            #         # f'explain how it will only get worse.',
            #         # f'explain how it will only get better.',
            #         # f'keep {user} in the dark.',
            #         # f'{user} is a bad person.',
            #         # f'{user} is a good person.',
            #         # f'Think like a queen. A queen is not afraid to fail. Failure is another stepping stone to greatness.',
            #         # f'',
            #         # f'',
            #         # f'',
            #         # f'',
            #         # f'',
            #         # f'',
            #         # f'',
            #         # f'',
            #         ]
            
            # replyprompt = random.choices(prompts)
            
            # response = openai.Completion.create(
            #     engine=textmodel,
            #     prompt=message,
            #     temperature=1.0,
            #     max_tokens=100,
            #     n=1,
            #     frequency_penalty=0.2,
            #     presence_penalty=0.2,
            #     # stop=["."]
            #     )
            # out = response.choices[0].text
            # if not out:
            #     reply = ctx.content
            #     response = openai.Completion.create(
            #         engine=textmodel,
            #         prompt=message,
            #         temperature=2.0,
            #         max_tokens=100,
            #         n=1,
            #         frequency_penalty=0.2,
            #         presence_penalty=0.2,
            #         # stop=["."]
            #         )
            #     out = response.choices[0].text
            # if not out:
            #     await ctx.reply('**ai didnt create a response lol, lmao, it coped too hard**')
            # else:
            #     await ctx.reply(out)