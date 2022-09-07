import shutil
import discord
import time
import json
import os
import re
import cogs.utils.functions as functions
from discord.ext import commands
from datetime import datetime, timezone

path = os.path.abspath(os.getcwd())
jsonpath = rf'{path}/cogs/log.json'

jsonmaxsize = 5242880

def _count_generator(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)

init = {
    "servers":[{
        "servername": "newserver",
        "serverID": 123,
        "channels":[{
            "channelname": "newchannel",
            "channelID": 456,                  
            "messages":[{
                "username": "newuser",
                "userID": 789,
                "message": "fukoff"
                }
            ]}
        ]}
    ]}

class logger(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('logger module online')

    @commands.Cog.listener()
    async def on_message(self, ctx):
        now_utc = str(datetime.now(timezone.utc))
        now_unix =  str(time.time())
        serverNAME = ctx.guild.name
        serverID = ctx.guild.id
        userNAME = ctx.author.name
        userID = ctx.author.id
        channelNAME = ctx.channel.name
        channelID = ctx.channel.id
        message = ctx.content
        
        reply = False
        if ctx.reference:
            reply = True
            print(f'╔═══ {ctx.reference.resolved.author.name}: {ctx.reference.resolved.content}')
        
        try:
            if message == "":
                message = ctx.attachments[0].url
        except Exception:
            try:
                message = ctx.attachments[0].proxy_url
            except Exception:
                return

        print(f'{userNAME}: {message}')

        if not reply:
            newserver = {
                "servername": serverNAME,
                "serverID": serverID,
                "channels":[{
                    "channelname": channelNAME,
                    "channelID": channelID,                  
                    "messages":[{
                        "username": userNAME,
                        "userID": userID,
                        "message": message,
                        "reply": reply,
                        "dateTime": now_utc,
                        "Unix": now_unix,
                        }]
                    }]
                }
            newchannel = {
                "channelname": channelNAME,
                "channelID": channelID,
                "messages":[{
                        "username": userNAME,
                        "userID": userID,
                        "message": message,
                        "reply": reply,
                        "dateTime": now_utc,
                        "Unix": now_unix,
                        }]
                    }
            newmessage = {
                "username": userNAME,
                "userID": userID,
                "message": message,
                "reply": reply,
                "dateTime": now_utc,
                "Unix": now_unix,
            }
        else:
            repliedmessage = ctx.reference.resolved.content
            replieduser = ctx.reference.resolved.author.name
            repliedID = ctx.reference.resolved.author.id
            newserverreplied = {
                "servername": serverNAME,
                "serverID": serverID,
                "channels":[{
                    "channelname": channelNAME,
                    "channelID": channelID,                  
                    "messages":[{
                        "username": userNAME,
                        "userID": userID,
                        "message": message,
                        "reply": reply,
                        "dateTime": now_utc,
                        "Unix": now_unix,
                        "replied too message":[{
                            "username": replieduser,
                            "userID": repliedID,
                            "message": repliedmessage,
                            }]
                        }]
                    }]
                }
            newchannelreplied = {
                "channelname": channelNAME,
                "channelID": channelID,
                "messages":[{
                    "username": userNAME,
                    "userID": userID,
                    "message": message,
                    "reply": reply,
                    "dateTime": now_utc,
                    "Unix": now_unix,
                    "replied too message":[{
                        "username": replieduser,
                        "userID": repliedID,
                        "message": repliedmessage,
                        }]
                    }]
                }
            newmessagereplied = {
                "username": userNAME,
                "userID": userID,
                "message": message,
                "reply": reply,
                "dateTime": now_utc,
                "Unix": now_unix,
                "replied too message":[{
                    "username": replieduser,
                    "userID": repliedID,
                    "message": repliedmessage,
                    }]
                }

        with open(jsonpath, 'r') as fin:
            file_data = json.load(fin)
        try:
            for servers in file_data["servers"]:
                if serverID == servers["serverID"]:
                    for channels in servers["channels"]:
                        if channelID == channels["channelID"]:
                            if reply:
                                channels["messages"].append(newmessagereplied)#if the channel exist post new message. with replied to message
                            else:
                                channels["messages"].append(newmessage)#if the channel exist post new message
                            raise StopIteration
                    if reply:
                        servers["channels"].append(newchannelreplied)#if the channel id doesnt excist post new channel, message. with replied to message
                    else:
                        servers["channels"].append(newchannel) #if the channel id doesnt excist post new channel, message
                    raise StopIteration
            if reply:
                file_data["servers"].append(newserverreplied) #if the server id doesnt exist post new server, channel, message. with replied to message
            else:
                file_data["servers"].append(newserver) #if the server id doesnt exist post new server, channel, message
        except StopIteration:
            pass 
        with open(jsonpath, 'w') as fout:
            json.dump(file_data, fout, indent = 4)

        '''
        Reset the json file to init when it gets too big but make a cold copy first.
        '''
        file_size = os.stat(jsonpath).st_size
        if file_size > jsonmaxsize:
            with open(jsonpath, 'rb') as fp:
                c_generator = _count_generator(fp.raw.read)
                count = sum(buffer.count(b'\n') for buffer in c_generator)
            
            shutil.copy(jsonpath, f'log {int(count/1000)}K.json')
            
            with open(jsonpath, 'w') as fnewout:
                json.dump(init, fnewout, indent = 4)

    '''
    Reset the json log the manual way if bot get slow or some bs. also make a cold copy first.
    '''
    @commands.has_permissions(administrator=True)  
    @commands.command(aliases=['resetlog'])
    async def reset(self, ctx,):
        with open(jsonpath, 'rb') as fp:
            c_generator = _count_generator(fp.raw.read)
            count = sum(buffer.count(b'\n') for buffer in c_generator)

        shutil.copy(jsonpath, f'log {int(count/1000)}K.json')

        with open(jsonpath, 'w') as fnewout:
            json.dump(init, fnewout, indent = 4)

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