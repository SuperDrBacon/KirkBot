from mimetypes import init
import discord
import random
import time
import typing
import asyncio
import json
import os
import re
from discord.ui import Button, View
from discord.ext import commands

jsonpath = os.path.abspath(os.getcwd()) + "/cogs/log.json"
messagestxt = os.path.abspath(os.getcwd()) + "/messages.txt"

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

        serverNAME = ctx.guild.name
        serverID = ctx.guild.id

        userNAME = ctx.author.name
        userID = ctx.author.id
        
        channelNAME = ctx.channel.name
        channelID = ctx.channel.id
        
        
        message = ctx.content
        try:
            if message == "":
                message = ctx.attachments[0].url
        except Exception:
            message = str(ctx.embeds[0])

        print(f'{userNAME}: {message}')


        newserver = {
                "servername": serverNAME,
                "serverID": serverID,
                "channels":[{
                    "channelname": channelNAME,
                    "channelID": channelID,                  
                    "messages":[{
                        "username": userNAME,
                        "userID": userID,
                        "message": message
                        }
                    ]}
                ]
            }

        newchannel = {
                "channelname": channelNAME,
                "channelID": channelID,
                "messages":[{
                        "username": userNAME,
                        "userID": userID,
                        "message": message
                        }
                    ]
                }

        newmessage = {
                "username": userNAME,
                "userID": userID,
                "message": message
            }


        with open(jsonpath, 'r') as fin:
            file_data = json.load(fin)

            try:
                for servers in file_data["servers"]:
                    if serverID == servers["serverID"]:
                        for channels in servers["channels"]:
                            if channels["channelID"] == channelID:
                                channels["messages"].append(newmessage)#if the channel exist post new message
                                raise StopIteration
                        servers["channels"].append(newchannel) #if the channel id doesnt excist post new channel, message
                        raise StopIteration
                file_data["servers"].append(newserver) #if the server id doesnt exist post new server, channel, message
            except StopIteration:
                pass 
        with open(jsonpath, 'w') as fout:
            json.dump(file_data, fout, indent = 4)
            
            
    @commands.command()
    async def getlog(self, ctx,):
        pass


    @commands.command()
    async def reset(self, ctx,):
        
        with open(jsonpath, 'w') as fout:
            json.dump(init, fout, indent = 4)
            
    @commands.has_permissions(administrator=True)      
    @commands.command(aliases=["up"])
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
                                
                                emojipattern = r'<.*?>'
                                text2 = re.sub(emojipattern, '', text)

                                commandpluspattern = r'\+([\S]+.)'
                                text3 = re.sub(commandpluspattern, '', text2)
                                
                                links = r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,10}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'
                                text4 = re.sub(links, '', text3)
                                
                                commanddotpattern = r'\.([\S]+.)'
                                text5 = re.sub(commanddotpattern, '', text4)
                                
                                commandcommapattern = r'\,([\S]+.)'
                                text6 = re.sub(commanddotpattern, '', text5)
                                
                                leadingspacespattern = r'^ +'
                                text7 = re.sub(leadingspacespattern, '', text6)
                                
                                exclamationpattern = r'\!([\S]+.)'
                                text8 = re.sub(exclamationpattern, '', text7)
                                
                                atpattern = r'\@([\S]+.)'
                                text9 = re.sub(atpattern, '', text8)
                                
                                # newline = '\n'
                                # text10 = re.sub(newline, ' ', text9)
                                
                                if not text9:
                                    continue
                                
                                messagein.write(text9+'\n')
                                imessage += 1
        after = (time.monotonic_ns() - before) / 1000000000
        await ctx.send(f'{after}s')
        await ctx.send(f'servers: {iserver} channels: {ichannel} messages: {imessage}')
            
            
def setup(bot):
    bot.add_cog(logger(bot))



# init = {
#     "servers":[{
#         "servername": serverNAME,
#         "serverID": serverID,
#         "channels":[{
#             "channelname": channelNAME,
#             "channelID": channelID,                  
#             "messages":[{
#                 "username": userNAME,
#                 "userID": userID,
#                 "message": message
#                 }
#             ]}
#         ]}
#     ]}