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
                                  ORDER, PERMISSIONS_DATABASE, TEXT_WORD_COUNT,
                                  MSG_DEL_DELAY)

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
    
    def ai_commands_enabled():
        """
        Custom check that verifies if AI commands are enabled in the channel.
        """
        async def predicate(ctx):
            cog = ctx.bot.get_cog("Ai")
            if cog:
                return await cog.check_channel_permissions(ctx)
            return True
        return commands.check(predicate)
    
    async def check_channel_permissions(self, ctx):
        r"""
        Check if AI commands are enabled in the current channel.
        
        Args:
            ctx: The command context with guild_id and channel_id
            
        Returns:
            bool: True if AI commands are enabled in the channel, False otherwise
        """
        if ctx.guild is None:  # Skip check in DMs
            return True
            
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('SELECT enabled FROM chatai WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)) as cursor:
                result = await cursor.fetchone()
                channel_enabled = result is not None and result[0]
        
        if not channel_enabled:
            await ctx.reply("AI commands are disabled in this channel.", delete_after=MSG_DEL_DELAY)
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            return False
        
        return True
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('AI module online')
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        guild_id = ctx.guild.id	
        channel_id = ctx.channel.id
        
        # Check if AI interaction is enabled in this channel
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
            async with con.execute('SELECT enabled FROM chatai WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)) as cursor:
                result = await cursor.fetchone()
                channel_enabled = result is not None and result[0]
        
        if not channel_enabled:
            return
            
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
        if random.randint(1, 600) == 1 and channel_enabled == 1 and not ctx.author.bot:
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
    @ai_commands_enabled()
    async def ai(self, ctx, *, message):
        '''
        Talk to the AI.
        The message is used as a prompt for the engine and the response is limited to 2000 characters.
        '''
        if ctx.message.reference:
            base = f'{ctx.message.reference.resolved.content}'
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