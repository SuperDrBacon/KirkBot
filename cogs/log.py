import discord
import time
import sqlite3
import os
import cogs.utils.functions as functions
from discord.ext import commands
from datetime import datetime, timezone

path = os.path.abspath(os.getcwd())
logdatabase = rf'{path}/cogs/log_data.db'

class logger(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        functions.checkForFile(os.path.dirname(logdatabase), os.path.basename(logdatabase), True)
    
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
            print(f'#{channel_name[:15]:<15} - ╔═══ {ctx.reference.resolved.author.name}: {ctx.reference.resolved.content}')
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
                con = sqlite3.connect(f'{path}/cogs/log_data.db')
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
                # cur.execute('SELECT max(id) FROM wordcount_data')
                # max_id = cur.fetchone()[0]
                # print("Record inserted successfully into wordcount_data table ", max_id)
            except Exception as error:
                print("Failed to insert multiple records into sqlite table:", error)
            finally:
                if con:
                    cur.close()
                    con.close()
                    # print("The SQLite connection is closed")
        else:
            try:
                con = sqlite3.connect(f'{path}/cogs/log_data.db')
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
                # cur.execute('SELECT max(id) FROM wordcount_data')
                # max_id = cur.fetchone()[0]
                # print("Record inserted successfully into wordcount_data table ", max_id)
            except Exception as error:
                print("Failed to insert multiple records into sqlite table:", error)
            finally:
                if con:
                    cur.close()
                    con.close()
                    # print("The SQLite connection is closed")

    '''
    Gets all the links in the channel and puts them in a file named the channel name.
    '''
    @commands.has_permissions(administrator=True)
    @commands.group(name='getlinks', invoke_without_command=True)
    async def getlinksbase(self, ctx, number:int):
        await ctx.message.delete()
        channelNAME = ctx.channel.name
        messages = await ctx.channel.history(limit=number, oldest_first=True).flatten()

        with open(f'{channelNAME}.txt', 'w', encoding='utf-8') as f:
            for message in messages:
                out = message.content
                if out.startswith('http'):
                    f.write(out+'\n')
            await ctx.channel.send('Got all messages in channel cause drink nut asked me again')
    
    @commands.has_permissions(administrator=True)
    @getlinksbase.command(name='all', invoke_without_command=True)
    async def getlinkall(self, ctx):
        # run through every channel, get all messages
        channellist = discord.Guild.text_channels
        threadlist = discord.Guild.threads
        pass


async def setup(bot):
    await bot.add_cog(logger(bot))

    # '''
    # get all the logged messages and put them in a file. and combine other files to make one big file.
    # '''
    # @commands.command(aliases=["up"])
    # @commands.has_permissions(administrator=True)      
    # async def update_mesages(self, ctx):
    #     iserver = 0
    #     ichannel = 0
    #     imessage = 0
    #     before = time.monotonic_ns()
    #     with open(jsonpath, 'r') as fin:
    #         file_data = json.load(fin)
    #     with open(messagestxt, 'w', encoding='utf-8') as messagein:  
    #         for servers in file_data["servers"]:
    #             if servers["serverID"] == 123 or servers["serverID"] == 937056927312150599:
    #                 continue
    #             iserver += 1
    #             for channels in servers["channels"]:
    #                 if channels["channelID"] == 939083691790061601 or channels["channelID"] == 939221538949980210:
    #                     ichannel += 1
    #                     for message in channels["messages"]:
    #                         text = str(message["message"])
    
    #                         if text == "[]":
    #                             continue
    
    #                         cleaned = functions.filter(text)

    #                         if not cleaned:
    #                             continue
    
    #                         messagein.write(cleaned+'\n')
    #                         imessage += 1
    #     totalLineCount = functions.joinfiles()
    #     after = (time.monotonic_ns() - before) / 1000000000
    #     await ctx.send(f'{after}s')
    #     await ctx.send(f'\n`servers: {iserver}`\n`channels: {ichannel}`\n`messages json: {imessage}`\n`total lines json+genAI: {totalLineCount}`')

    # @commands.command(aliases=["getlink"])
    # async def getlinks(self, ctx):
    #     messages = await ctx.channel.history(limit=123).flatten()