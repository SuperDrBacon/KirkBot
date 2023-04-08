import discord
import time
import sqlite3
import os
import cogs.utils.functions as functions
from discord.ext import commands
from datetime import datetime, timezone

ospath = os.path.abspath(os.getcwd())
log_database = rf'{ospath}/cogs/log_data.db'

class logger(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        functions.checkForFile(os.path.dirname(log_database), os.path.basename(log_database), True, 'log')
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('logger module online')

    @commands.Cog.listener()
    async def on_message(self, ctx):
        server_name = ctx.guild.name
        server_id= ctx.guild.id
        channel_name = ctx.channel.name
        channel_id = ctx.channel.id
        user_name = ctx.author.name
        user_id = ctx.author.id
        message = ctx.content
        message_id = ctx.id
        reply = 0
        now_utc = str(datetime.now(timezone.utc))
        now_unix = str(time.time())
        
        if ctx.reference:
            reply = 1
            print(f'                 ╔═══ {ctx.reference.resolved.author.name}: {ctx.reference.resolved.content}')
            original_username = ctx.reference.resolved.author.name
            original_username_id = ctx.reference.resolved.author.id
            original_message = ctx.reference.resolved.content
            original_message_id = ctx.reference.resolved.id
        
        try:
            if message == "":
                message = ctx.attachments[0].url
        except Exception:
            try:
                message = ctx.attachments[0].proxy_url
            except Exception:
                return
        
        print(f'#{channel_name[:15]:<15} - {user_name}: {message}')
        
        if reply == 1:
            try:
                con = sqlite3.connect(f'{ospath}/cogs/log_data.db')
                cur = con.cursor()
                data_to_inset = '''INSERT INTO log_data(
                            SERVER_NAME,
                            SERVER_ID,
                            CHANNEL_NAME,
                            CHANNEL_ID,
                            USERNAME,
                            USER_ID,
                            MESSAGE,
                            MESSAGE_ID,
                            IS_REPLY,
                            ORIGINAL_USERNAME,
                            ORIGINAL_USER_ID,
                            ORIGINAL_MESSAGE,
                            ORIGINAL_MESSAGE_ID,
                            DATE_TIME,
                            UNIX_TIME) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'''
                data_tuple = (
                            server_name, 
                            server_id, 
                            channel_name, 
                            channel_id, 
                            user_name, 
                            user_id, 
                            message, 
                            message_id, 
                            reply, 
                            original_username, 
                            original_username_id, 
                            original_message, 
                            original_message_id, 
                            now_utc,
                            now_unix)
                cur.execute(data_to_inset, data_tuple)
                con.commit()
            
            except Exception as error:
                print("Failed to insert multiple records into sqlite table:", error)
            finally:
                if con:
                    cur.close()
                    con.close()
        else:
            try:
                con = sqlite3.connect(f'{ospath}/cogs/log_data.db')
                cur = con.cursor()
                data_to_inset = '''INSERT INTO log_data(
                            SERVER_NAME,
                            SERVER_ID,
                            CHANNEL_NAME,
                            CHANNEL_ID,
                            USERNAME,
                            USER_ID,
                            MESSAGE,
                            MESSAGE_ID,
                            IS_REPLY,
                            DATE_TIME,
                            UNIX_TIME) VALUES (?,?,?,?,?,?,?,?,?,?,?);'''
                data_tuple = (
                            server_name, 
                            server_id, 
                            channel_name, 
                            channel_id, 
                            user_name, 
                            user_id, 
                            message, 
                            message_id, 
                            reply, 
                            now_utc,
                            now_unix)
                cur.execute(data_to_inset, data_tuple)
                con.commit()
            
            except Exception as error:
                print("Failed to insert multiple records into sqlite table:", error)
            finally:
                if con:
                    cur.close()
                    con.close()

    '''
    Gets all the links in the channel and puts them in a file named the channel name.
    '''
    @commands.has_permissions(administrator=True)
    @commands.group(name='getlinks', invoke_without_command=True)
    async def getlinksbase(self, ctx, number:int=100000000):
        await ctx.message.delete()
        channelNAME = ctx.channel.name
        messages = await ctx.channel.history(limit=number, oldest_first=True).flatten()
        
        with open(f'{channelNAME}.txt', 'w', encoding='utf-8') as f:
            for message in messages:
                out = message.content
                if out.startswith('http'):
                    f.write(out+'\n')
            await ctx.channel.send('Got all messages in channel cause drink nut asked me again')

async def setup(bot):
    await bot.add_cog(logger(bot))