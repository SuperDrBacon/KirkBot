# import datetime
import random
import re
import sqlite3
from collections import defaultdict

import aiosqlite
import discord
import ollama
from discord.ext import commands

from cogs.utils.constants import (ARCHIVE_DATABASE, BOTID, MEME_WORD_COUNT,
                                  ORDER, PERMISSIONS_DATABASE, TEXT_WORD_COUNT)

textmodel = 'dpun'

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
        guild_id = ctx.guild.id	
        channel_id = ctx.channel.id
        #replies to messages that mention the bot
        if ctx.content.startswith(f'<@!{BOTID}>') or ctx.content.startswith(f'<@{BOTID}>'):
            con = sqlite3.connect(ARCHIVE_DATABASE)
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
        if not ctx.author.bot and ctx.reference and int(ctx.reference.resolved.author.id) == int(BOTID):
            base = f'{ctx.reference.resolved.content}'
            # reply = f'{ctx.author.name}: {ctx.content}'
            reply = f'{ctx.content}'
            
            message_log = [
                {"role": "system", "content": "Respond to this conversation with a short reply."},
                {"role": "user", "content": base},
                {"role": "user", "content": reply}
            ]
            response = ollama.chat(model=textmodel, messages=message_log)
            if response:
                await ctx.reply(response['message']['content'][:2000])
            else:
                response = ollama.chat(model=textmodel, messages=message_log)
                if response:
                    await ctx.reply(response['message']['content'][:2000])
                else:
                    await ctx.reply('I am sorry, I am unable to generate a response at this time. -God')
        
        #replies to messages in channels that have the AI enabled
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('SELECT enabled FROM chatai WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)) as cursor:
                channel_enabled = (result := await cursor.fetchone()) is not None and result[0]
        
        if random.randint(1, 60) == 1 and channel_enabled == 1 and not ctx.author.bot:
            '''
            get the last 15 messages from the channel and generate a response
            '''
            messages = [message async for message in ctx.channel.history(limit=15, oldest_first=False)]
            messages.reverse()
            message_log = [{"role": "system", "content": "Respond to this conversation with a short reply."}]
            for message in messages:
                if message.content and not re.search(r'(https?://\S+)', message.content):
                    message_log.append({
                        "role": "user",
                        # "content": f"{message.author.display_name}: {message.content}"
                        "content": f"{message.content}"
                    })
            response = ollama.chat(model=textmodel, messages=message_log)
            if response:
                await ctx.reply(response['message']['content'][:2000])
            else:
                response = ollama.chat(model=textmodel, messages=message_log)
                if response:
                    await ctx.reply(response['message']['content'][:2000])
                else:
                    await ctx.reply('I am sorry, I am unable to generate a response at this time. -God')
    
    @commands.command(name='ai')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ai(self, ctx, *, message):
        '''
        Talk to the AI.
        The message is used as a prompt for the engine and the response is limited to 2000 characters.
        '''
        if ctx.message.reference:
            # base = f'{ctx.message.reference.resolved.author.name}: {ctx.message.reference.resolved.content}'
            base = f'{ctx.message.reference.resolved.content}'
            # reply = f'{ctx.author.name}: {message}'
            reply = f'{message}'
            
            message_log = [
                {"role": "system", "content": "Respond to this conversation with a short reply."},
                {"role": "user", "content": base},
                {"role": "user", "content": reply}
            ]
            response = ollama.chat(model=textmodel, messages=message_log)
            if response:
                await ctx.reply(response['message']['content'][:2000])
            else:
                response = ollama.chat(model=textmodel, messages=message_log)
                if response:
                    await ctx.reply(response['message']['content'][:2000])
                else:
                    await ctx.reply('I am sorry, I am unable to generate a response at this time. -God')
        else:
            message_log = [
                {'role': 'system', 'content': 'Respond to this conversation with a short reply.'},
                {'role': 'user', 'content': message}
            ]
            response = ollama.chat(model=textmodel, messages=message_log)
            if response:
                await ctx.reply(response['message']['content'][:2000])
            else:
                response = ollama.chat(model=textmodel, messages=message_log)
                if response:
                    await ctx.reply(response['message']['content'][:2000])
                else:
                    await ctx.reply('I am sorry, I am unable to generate a response at this time. -God')
    
async def setup(bot):
    await bot.add_cog(Ai(bot))
    
    # @commands.command(name='meme')
    # @commands.cooldown(1, 5, commands.BucketType.user)
    # async def meme(self, ctx, member: discord.Member = None):
    #     imagefile = BytesIO()
    #     guild_id = ctx.guild.id	
    #     channel_id = ctx.channel.id
        
    #     #pull a random user profile picture
    #     guild = self.bot.get_guild(ctx.guild.id)
    #     if member is None:
    #         while member is None:
    #             potential_member = random.choice(guild.members)
    #             try:
    #                 avatar_bytes = await potential_member.avatar.read()
    #                 member = potential_member
    #             except AttributeError:
    #                 pass
    #     else:
    #         try:
    #             avatar_bytes = await member.avatar.read()
    #         except AttributeError:
    #             await ctx.reply('**This user has no avatar.**', delete_after=5)
    #             await ctx.message.delete(delay=5)
    #             return
    #     avatar = Image.open(BytesIO(avatar_bytes))
    #     avatar = avatar.resize((1024, 1024))
    #     # avatar.save(imagefile, format='PNG')
    #     # imagefile.seek(0)
    #     # await ctx.send(file=discord.File(imagefile, filename='meme.png'))
        
    #     con = sqlite3.connect(f'{OSPATH}/cogs/archive_data.db')
    #     con.row_factory = lambda _, row: row[0]
    #     cur = con.cursor()
    #     # text = cur.execute('SELECT message FROM archive_data WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)).fetchall()
    #     text = cur.execute('SELECT message FROM archive_data').fetchall()
        
    #     # Filter out messages containing links
    #     filtered_text = [line for line in text if not re.search(r'(https?://\S+)', line)]
    #     corpus = ' '.join(' '.join(line.split()) for line in filtered_text)
        
    #     chain = MarkovChain(order=ORDER)
    #     chain.add_text(corpus)
    #     chain.calculate_word_weights()
        
    #     def get_text():
    #         # Generating text using the generator function
    #         generated_text_generator = chain.generate_text_incremental(text_word_count=MEME_WORD_COUNT)
    #         generated_text = ' '.join(word for word in generated_text_generator)
    #         return generated_text
        
    #     top_text = get_text()
    #     bottom_text = get_text()
        
    #     font = ImageFont.truetype(IMAGEPATH+'impact.ttf', 60)
    #     draw = ImageDraw.Draw(avatar)
        
    #     text_color = (237, 230, 211)
    #     # Draw top text
    #     text_bounding_box = font.getbbox(top_text)
    #     text_width = text_bounding_box[2] - text_bounding_box[0]
    #     text_height = text_bounding_box[3] - text_bounding_box[1]
    #     text_position = ((avatar.width - text_width) / 2, 0)
    #     draw.text(text_position, top_text, font=font, fill=text_color)
        
    #     # Draw bottom text
    #     text_bounding_box = font.getbbox(bottom_text)
    #     text_width = text_bounding_box[2] - text_bounding_box[0]
    #     text_height = text_bounding_box[3] - text_bounding_box[1]
    #     text_position = ((avatar.width - text_width) / 2, avatar.height - text_height)
    #     draw.text(text_position, bottom_text, font=font, fill=text_color)
        
    #     # save to send
    #     avatar.save(imagefile, format='PNG')
    #     imagefile.seek(0)

    #     await ctx.send(file=discord.File(imagefile, filename='meme.png'))