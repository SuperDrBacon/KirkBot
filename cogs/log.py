from mimetypes import init
import discord
import random
import time
import typing
import asyncio
import discord_components
import json
import os
import pandas as pd
from treelib import Node, Tree
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
# tree = Tree()

# guild = 'discord.Guild.name'
# guild = 'servers'
# user = 'users'
# channel = 'channels'
# tree.create_node(guild, 'server')
# tree.create_node(user, 'user', parent='server')
# tree.create_node(channel, 'channel', parent='user')

class logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # guild = discord.Guild.name
        # tree.create_node(guild, 'server')
        # tree.create_node('user', parent='server')
        # tree.create_node('channel', parent='user')

    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print('logger module online')
        # guild = discord.Guild.name
        # tree.create_node(guild, 'server')
        # tree.create_node('user', parent='server')
        # tree.create_node('channel', parent='user')
    
    
    @commands.Cog.listener()
    async def on_message(self, ctx): 
        # if ctx.guild.id != 937056927312150599:
        #     return
        # if ctx.author.id != 931276237157068850:
        #     print(f'{ctx.author}: {ctx.content}')
        
            # return
        # else: return
        
        serverNAME = ctx.guild.name
        serverID = ctx.guild.id

        userNAME = ctx.author.name
        userID = ctx.author.id
        
        channelNAME = ctx.channel.name
        channelID = ctx.channel.id
        
        
        message = ctx.content
        if message == "":
            message = ctx.attachments[0].url
            # for i in ctx.attachments:
            #     for j in len(i):
            #         temp = i
            #         temp2 = str(temp)
            #         temp2.join(', ')
            # message = temp2
            # if message is None:
            #     message = ctx.attachments[1].url
            #     if message is None:
            #         message = '---prob a sticker reply'
        
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
        
        with open(jsonpath, 'r') as fin:
            file_data = json.load(fin)
            # for servers in file_data["servers"]:
            #     # print(servers)
            #     print(servers["serverID"])
            #     print(serverID)
            #     if servers["serverID"] == serverID:
            #         print("ytes")
            #         for channels in servers["channels"]:
            #             print(channels)
            #     else:
            #         print("no \n")
            
            
            try:
                for servers in file_data["servers"]:
                    if serverID == servers["serverID"]:
                        for channels in servers["channels"]:
                            if channels["channelID"] == channelID:
                                channels["messages"].append(newmessage)#if the channel exists poste new message
                                raise StopIteration
                        servers["channels"].append(newchannel) #if the channel id doesnt excst poste new channel, message
                        raise StopIteration
                file_data["servers"].append(newserver) #if the server id doesnt exist poste new server, channel, message
            except StopIteration:
                pass 
        with open(jsonpath, 'w') as fout:
            json.dump(file_data, fout, indent = 4)
            
            
    @commands.command()
    async def getlog(self, ctx,):
        pass
        # with open(jsonpath, 'r') as f:
        #     jsondata = json.load(f)

        # new = await iterate_multidimensional(jsondata)
        # await ctx.send(new)
        

            # try:
            #     for servers in file_data["servers"]:
            #         if serverID == servers["serverID"]:
            #             for channels in servers["channels"]:
            #                 if channelID == channels["channelID"]:
            #                     channels[-1].append(newmessage)#if the channel exists poste new message
            #                     raise StopIteration
            #                 else:
            #                     servers[-1].append(newchannel) #if the channel id doesnt excst poste new channel, message
            #                     raise StopIteration
            #         else:
            #             file_data[-1].append(newserver) #if the server id doesnt exist poste new server, channel, message
            #             raise StopIteration
            # except StopIteration:
            #     pass 

            # try:
            #     for servers in file_data["servers"]:
            #         if serverID != servers["serverID"]:
            #             file_data["servers"].append(newserver) #if the server id doesnt exist poste new server, channel, message
            #             raise StopIteration
            #         else:
            #             for channels in servers["channels"]:
            #                 if channelID != channels["channelID"]:
            #                     servers["channels"].append(newchannel) #if the channel id doesnt excst poste new channel, message
            #                     raise StopIteration
            #                 else:
            #                     channels["messages"].append(newmessage)#if the channel exists poste new message
            #                     raise StopIteration
            # except StopIteration:
            #     pass 

    @commands.command()
    async def reset(self, ctx,):
        
        with open(jsonpath, 'w') as fout:
            json.dump(init, fout, indent = 4)







#######################functions################################       
        
# async def iterate_multidimensional(my_dict):
#     for k,v in my_dict.items():
#         if(isinstance(v,dict)):
#             print(k+":")
#             iterate_multidimensional(v)
#             continue
#         return(k+" : "+str(v))

def setup(bot):
    bot.add_cog(logger(bot))
    
    
    
    
    
    
            # for i in range(len(file_data["servers"])):
            #     if serverID == file_data["servers"][i]["serverID"]:
                    
            #         for j in range(len(file_data["servers"]["channels"])):
            #             if channelID == file_data["servers"]["serverID"][j]["channelID"]:
            #                 file_data["servers"]["channels"]["messages"].append(newmessage)
            #                 break
            #             else: 
            #                 file_data["servers"]["channels"].append(newchannel)
            #                 break
            #     else:
            #         file_data["servers"].append(newserver)
            #         break
                    
                    
                    
            # json.dump(logdik, f, indent = 4)
            # Join new_data with file_data inside emp_details
            
            # for i in file_data["servers"]:
            #     if not i == serverNAME:
            #         file_data["servers"][i] = serverNAME
            #         file_data["servers"]["channels"] = channel
            #         file_data["servers"]["channels"]["users"] = user
            #         file_data["servers"]["channels"]["users"]["messages"] = message
                    
                    
                # for _channel in file_data["channels"][0]:
                #     if not _channel == channel:
                #         file_data["channels"] = channel
                        
                #     for _user in file_data["servers"]["channels"]["users"]:
                #         if not _user == user:
                #             file_data["servers"]["channels"]["users"] = user
                #         file_data["servers"]["channels"]["users"]["messages"] = message





            # file_data[serverNAME][channel][user].append(message)
            # Sets file's current position at offset.
            # file.seek(0)
            # convert back to json.
            # json.dump(file_data, f, indent = 4)
            
            
        # if serverNAME != guild:
        #     tree.create_node(serverNAME, parent='server')
        
        # tree.create_node('user', parent='server', data=user)
        # tree.create_node('channel', parent='user', data=channel)
        # tree.create_node('message', parent='channel', data=message)

        # print(f'content {ctx.content}')
        # print(f'message id {ctx.id}')
        # print(f'channel id {ctx.channel.id}')

        # await ctx.send(jsondata["servers"][0]["servername"])
        
        # for ek1 in jsondata:
        #     await ctx.send(jsondata["servers"][ek1]["servername"])
        #     # await ctx.send(jsondata["servers"][ek1]["servername"][0]["channelname"])
        #     for ek2 in jsondata["servers"][ek1]["channels"]:
        #         await ctx.send(jsondata["servers"][ek1]["channels"][ek2]["channelname"])
        
        
        
        # for key1, key2 in jsondata:
        #     # await ctx.send(f'{key1, key2, key3} : {jsondata[key1][key2][key3]} \n')
        #     await ctx.send("Key: " + key1)
        #     # await ctx.send("Value: " + str(key2))
        #     for key3, key4 in key2.items():
        #         await ctx.send("Key: " + key3 + "Value: " + str(key4))
        
        
        
        # tree.show()
        # f = open('./other/boom.txt', 'w')  
        # f.write('')
        # f.close()

        # tree.save2file('./other/boom.txt')
        # await ctx.send('zond log')






# {
#     "servers": {
#         "channels": {
#             "user": {
#             }
#         }
#     }
# }