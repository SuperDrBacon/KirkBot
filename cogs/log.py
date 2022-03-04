import discord
import time
import json
import os
import re
import cogs.utils.functions as functions
from discord.ui import Button, View
from discord.ext import commands
from datetime import datetime, timezone

jsonpath = os.path.dirname(os.path.realpath(__file__)) + "\\log.json"
messagestxt = os.path.dirname(os.path.realpath(__file__)) + "\\jsonLogToMessages.txt"
genAI_log = os.path.dirname(os.path.realpath(__file__)) + "\\genAI_log.txt"

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
            # try:
            message = str(f'{ctx.embeds[0]}')
            # except Exception:
            #     message = '.-prob a sticker-.'

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
            
            
    @commands.command()
    async def getlog(self, ctx,):
        pass

    @commands.command()
    @commands.has_permissions(administrator=True)  
    async def reset(self, ctx,):
        pass
        # with open(jsonpath, 'w') as fout:
        #     json.dump(init, fout, indent = 4)
            
    @commands.command(aliases=["up"])
    @commands.has_permissions(administrator=True)      
    async def update_mesages(self, ctx):
        iserver = 0
        ichannel = 0
        imessage = 0
        before = time.monotonic_ns()
        with open(jsonpath, 'r') as fin:
            file_data = json.load(fin)
        with open(messagestxt, 'w', encoding='utf-8') as messagein:  
            for servers in file_data["servers"]:
                if servers["serverID"] == 123 or servers["serverID"] == 937056927312150599:
                    continue
                iserver += 1
                for channels in servers["channels"]:
                    if channels["channelID"] == 939083691790061601 or channels["channelID"] ==939221538949980210:
                        ichannel += 1
                        for message in channels["messages"]:
                            text = str(message["message"])
                            
                            if text == "[]":
                                continue
                            
                            cleaned = functions.filter(text)
                            
                            if not cleaned:
                                continue
                            
                            messagein.write(cleaned+'\n')
                            imessage += 1
        totalLineCount = functions.joinfiles()
        after = (time.monotonic_ns() - before) / 1000000000
        await ctx.send(f'{after}s')
        await ctx.send(f'\n`servers: {iserver}`\n`channels: {ichannel}`\n`messages json: {imessage}`\n`total lines json+genAI: {totalLineCount}`')

    # @commands.command(aliases=["getlink"])
    # async def getlinks(self, ctx):
    #     messages = await ctx.channel.history(limit=123).flatten()
    
    @commands.has_permissions(administrator=True)
    @commands.group(name='getlinks', invoke_without_command=True)
    async def getlinksbase(self, ctx, number:int):
        await ctx.message.delete()
        channelNAME = ctx.channel.name
        counter = 0
        messages = await ctx.channel.history(limit=number, oldest_first=True).flatten()
        # loop each message to check for phrase
        with open(f'{channelNAME}.txt', 'w', encoding='utf-8') as f:
            for message in messages:
                out = message.content
                # print(out)
                f.write(out+'\n\n---------\n\n')
        # await ctx.channel.send('got all messages in channel cause drink nut keeps dm-ing me')
            # print(message.content)
            # newmessage = functions.isLink(message.content)
        #     if functions.isLink(message.content):
        #         print(123)
        #         counter += 1
        #         total += str(message)
        # await ctx.channel.send(f'{counter} messages')
        # await ctx.channel.send(f'{total} messages')
    
    @commands.has_permissions(administrator=True)
    @getlinksbase.command(name='list', invoke_without_command=True)
    async def getlinklist(self, ctx):
        links = functions.getLink()



def setup(bot):
    bot.add_cog(logger(bot))
