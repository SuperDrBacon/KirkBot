import asyncio
import json
import os
import discord
import datetime as dt
import cogs.utils.functions as functions
from textwrap import indent
from discord.ext import commands

ospath = os.path.abspath(os.getcwd())
basedListPath = rf'{ospath}/cogs/basedList.json'

init = {
    "servers":[{
        "serverID": 956247196699860992,
        "list":{
            1: "link",
            2: "link",
            }
        }
    ]}

class Music(commands.Cog):
    '''
    This module represents a music module in a Discord bot. It provides functionalities related to managing a based list, which is a collection of songs.
    '''
    def __init__(self, bot):
        self.bot = bot
        functions.checkForFile(os.path.dirname(basedListPath), os.path.basename(basedListPath))
        if os.stat(basedListPath).st_size == 0:
            with open(basedListPath, 'w') as f:
                json.dump(init, f, indent=4)          

    @commands.Cog.listener()
    async def on_ready(self):
        print("Music module is online")
    
    @commands.group(name='basedlist', aliases=['bl'], invoke_without_command=True)
    async def basedList_base(self, ctx):
        '''
        Based list
        '''	
        contents = ["This is page 1!", "This is page 2!", "This is page 3!", "This is page 4!"]
        pages = len(contents)
        cur_page = 1
        embed = discord.Embed(title=f"Based List", description=f'Page {cur_page}/{pages}:\n{contents[cur_page-1]}', color=0x00ff00, timestamp=dt.datetime.utcnow())
        message = await ctx.send(embed=embed)
        # getting the message object for editing and reacting

        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]
            # This makes sure nobody except the command sender can interact with the "menu"

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=100, check=check)
                # waiting for a reaction to be added - times out after x seconds, 60 in this
                # example

                if str(reaction.emoji) == "▶️" and cur_page != pages:
                    cur_page += 1
                    await message.edit(content=f"Page {cur_page}/{pages}:\n{contents[cur_page-1]}")
                    await message.remove_reaction(reaction, user)

                elif str(reaction.emoji) == "◀️" and cur_page > 1:
                    cur_page -= 1
                    await message.edit(content=f"Page {cur_page}/{pages}:\n{contents[cur_page-1]}")
                    await message.remove_reaction(reaction, user)

                else:
                    await message.remove_reaction(reaction, user)
                    # removes reactions if the user tries to go forward on the last page or
                    # backwards on the first page
            except asyncio.TimeoutError:
                await message.delete()
                break
                # ending the loop if user doesn't react after x seconds
    
    @basedList_base.command(name='add')
    async def basedList_add(self, ctx, link:str):
        '''
        Add a song to the based list.
        '''
        await ctx.send("Added song to list")
        with open (basedListPath, 'r') as f:
            basedList = json.load(f)
        
        # with open (basedListPath, 'w') as f:
        #     json.dump(init, f, indent=4)
        
        serverID = ctx.guild.id
        
        for server in basedList['servers']:
            if serverID == server["serverID"]:
                keylist = list(server["list"].keys())
                print (keylist)
                newItem = {len(keylist)+1: link}
                server["list"].update(newItem)
                break
        else:
            basedList['servers'].append({"serverID": serverID, "list": {1: link}})
            
        with open (basedListPath, 'w') as f:
            json.dump(basedList, f, indent=4)	


async def setup(bot):
    await bot.add_cog(Music(bot))
