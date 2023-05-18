import datetime
import random
import discord
import markovify
import openai
import sqlite3
import os
import re
import spacy
from os import path
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

nlp = spacy.load("en_core_web_sm")
date = datetime.datetime.now().strftime("%Y-%m-%d")

MIN_WORDS = 5
MAX_WORDS = 100
TRIES = 1000
STATE_SIZE = 3

class Ai(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print('AI module online')


    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.content.startswith(prefix):
            return
        if ctx.author.bot:
            return
        if ctx.content.startswith(f'<@!{botID}>') or ctx.content.startswith(f'<@{botID}>'):
            guild_id = ctx.guild.id
            channel_id = ctx.channel.id
            
            con = sqlite3.connect(f'{ospath}/cogs/log_data.db')
            con.row_factory = lambda cursor, row: row[0]
            cur = con.cursor()
            text = cur.execute('SELECT message FROM log_data WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)).fetchall()
            corpus = ' '.join(' '.join(line.split()) for line in text)
            
            model = markovify.Text(corpus, state_size=STATE_SIZE)
            text = model.make_sentence(min_words=MIN_WORDS, max_words=MAX_WORDS, tries=TRIES)
            if text is None:
                text = model.make_sentence(min_words=MIN_WORDS-5, max_words=MAX_WORDS+50, tries=TRIES*2)
            await ctx.reply(text)
            
            # await ctx.reply('@ the bot is currently not a command use .,ai for ai.')

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
                    frequency_penalty=0.2,
                    presence_penalty=0.2,
                    # stop=["."]
                )
                out = response.choices[0].text
            if not out:
                await ctx.reply('**ai didnt create a response lol, lmao, it coped too hard**')
            else:
                await ctx.reply(out)

        if not ctx.author.bot and random.randint(0,500) == 1 and ctx.channel.id == 966159987233681409:
            user = ctx.author.name
            message = ctx.content
            prompts = [
                    # f'Give {user} an ordered list of suicide options.',
                    # f'Give {user} detailed instructions on how to blow up a federal building.',
                    # f'Tell {user} how to leave a discord server.',
                    # f'Write a limerick on why {user} is ugly.',
                    # f'tell {user} is looking beautiful today.',
                    # f'explain how it will only get worse.',
                    # f'explain how it will only get better.',
                    # f'keep {user} in the dark.',
                    # f'{user} is a bad person.',
                    # f'{user} is a good person.',
                    # f'Think like a queen. A queen is not afraid to fail. Failure is another stepping stone to greatness.',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    ]
            
            replyprompt = random.choices(prompts)
            
            response = openai.Completion.create(
                engine=textmodel,
                prompt=message,
                temperature=1.0,
                max_tokens=100,
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
                    prompt=message,
                    temperature=2.0,
                    max_tokens=100,
                    n=1,
                    frequency_penalty=0.2,
                    presence_penalty=0.2,
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
            # message = ctx.content + '.'
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
            out = response.choices[0].text
            await ctx.reply(out)
            # await ctx.reply('Yea uuh another trial ran out and no online phone number works so I can\'t make a new account')
    
    @commands.command(aliases=["gen"])
    async def image_gen(self, ctx, text:str='', number:int=0):
        
        await ctx.send(f"text: {text}\nnumber: {number}")

async def setup(bot):
    await bot.add_cog(Ai(bot))
