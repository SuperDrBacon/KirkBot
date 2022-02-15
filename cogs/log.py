from mimetypes import init
import discord
import random
import time
import typing
import asyncio
import json
import os
import pandas as pd
from discord.ui import Button, View
from discord.ext import commands

jsonpath = os.path.abspath(os.getcwd()) + "/cogs/log.json"


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