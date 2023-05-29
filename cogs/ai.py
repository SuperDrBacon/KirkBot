# import datetime
import random
import discord
import openai
import sqlite3
import os
from collections import defaultdict
from discord.ext import commands
from configparser import ConfigParser

ospath = os.path.abspath(os.getcwd())
config = ConfigParser()
config.read(rf'{ospath}/config.ini')

key = config['BOTCONFIG']['openaiAPI']
botID = config['BOTCONFIG']['botID']
prefix = config['BOTCONFIG']['prefix']
openai.api_key = key
textmodel = 'text-curie-001'
# textmodel = 'text-davinci-003'

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
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print('AI module online')


    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.id == 974297735559806986 and random.randint(0,3) == 1: #GenAI schizo rambling bot. it will reply to this bot by rambling its own schizo ramblings
            guild_id = ctx.guild.id	
            channel_id = ctx.channel.id
            con = sqlite3.connect(f'{ospath}/cogs/log_data.db')
            con.row_factory = lambda cursor, row: row[0]
            cur = con.cursor()
            text = cur.execute('SELECT message FROM log_data WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)).fetchall()
            
            corpus = ' '.join(' '.join(line.split()) for line in text)
            
            chain = MarkovChain(order=4)
            chain.add_text(corpus)
            chain.calculate_word_weights()
            
            # Generating text using the generator function
            generated_text_generator = chain.generate_text_incremental(text_word_count=30)
            generated_text = ' '.join(word for word in generated_text_generator)
            await ctx.reply(generated_text)
        
        if ctx.content.startswith(f'<@!{botID}>') or ctx.content.startswith(f'<@{botID}>'):
            guild_id = ctx.guild.id	
            channel_id = ctx.channel.id
            con = sqlite3.connect(f'{ospath}/cogs/log_data.db')
            con.row_factory = lambda cursor, row: row[0]
            cur = con.cursor()
            text = cur.execute('SELECT message FROM log_data WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)).fetchall()
            
            corpus = ' '.join(' '.join(line.split()) for line in text)
            
            chain = MarkovChain(order=4)
            chain.add_text(corpus)
            chain.calculate_word_weights()
            
            # Generating text using the generator function
            generated_text_generator = chain.generate_text_incremental(text_word_count=30)
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
        
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ai(self, ctx, *, message):
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