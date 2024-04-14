import asyncio
import datetime
import os
import discord
import aiosqlite
import cogs.utils.functions as functions

from configparser import ConfigParser
from discord import Embed
from discord.ext import commands, tasks

ospath = os.path.abspath(os.getcwd())
config, info = ConfigParser(), ConfigParser()
config.read(rf'{ospath}/config.ini')
info.read(rf'{ospath}/info.ini')

prefix = config['BOTCONFIG']['prefix']
invitelog_database = rf'{ospath}/cogs/invitelog_data.db'
command_prefix = config['BOTCONFIG']['prefix']
botversion = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']

MSG_DEL_DELAY = 10
SECOND_LOOP_DELAY = 5

class Invitelog(commands.Cog):
    '''
    The Invitelog module contains all commands related to the Invitelog feature.
    This module logs information about invites on the server, including the inviter, the invite code, the invite channel, \
    the expiration date, and the number of uses.
    '''
    def __init__(self, bot):
        self.bot = bot
        self.update_invites_task = None
        if not self.update_invites_task or self.update_invites_task.done():
            self.update_invites_task = asyncio.create_task(self.update_invites_loop())
        functions.checkForFile(filepath=os.path.dirname(invitelog_database), filename=os.path.basename(invitelog_database), database=True, dbtype='invitelog')
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.update_invites()
        print('InviteLog module is online')
    
    async def update_invites(self):
        async with aiosqlite.connect(invitelog_database) as con:
            async with con.cursor() as cur:
                # Loop through each server
                for server in self.bot.guilds:
                    # Get the current invites for the server
                    invites = await server.invites()
                    
                    # Update the database with the new invite information
                    for invite in invites:
                        await cur.execute("SELECT * FROM invitelog WHERE SERVER_ID = ? AND INVITE_CODE = ?", (server.id, invite.code))
                        existing_invite = await cur.fetchone()
                        if existing_invite:
                            # Update the existing invite
                            await cur.execute("UPDATE invitelog SET CURRENT_USES = ? WHERE SERVER_ID = ? AND INVITE_CODE = ?;", (invite.uses, server.id, invite.code))
                        else:
                            # Add a new invite
                            await cur.execute("INSERT INTO invitelog(SERVER_ID, INVITE_CODE, CURRENT_USES, MAX_USES, INVITER_ID, INVITER_NAME, INVITE_CHANNEL_ID, EXPIRATION_DATE_UNIX) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                                            (server.id, invite.code, invite.uses, invite.max_uses, invite.inviter.id, invite.inviter.name, invite.channel.id, (invite.expires_at.timestamp() if invite.expires_at else 0)))
                    
                    # Remove any invites that are no longer active
                    await cur.execute("SELECT INVITE_CODE FROM invitelog WHERE SERVER_ID = ?", (server.id,))
                    db_invites = [row[0] for row in await cur.fetchall()]
                    for db_invite in db_invites:
                        if db_invite not in [invite.code for invite in invites]:
                            await cur.execute("DELETE FROM invitelog WHERE SERVER_ID = ? AND INVITE_CODE = ?", (server.id, db_invite))
                            # await cur.execute("DELETE FROM users WHERE INVITE_CODE = ?", (db_invite,)) # dont remove the users from the users table as this is a log of all users that have joined a server
            
            await con.commit()
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        self.update_invites_task.cancel()
        
        log_channel_id = 1153340486661185580  # glowing invites channel
        log_channel = self.bot.get_channel(log_channel_id)
        
        embed = discord.Embed(title="New member joined", color=0x00ff00)
        embed.add_field(name="Member", value=f"{member.mention} (ID: {member.id})", inline=False)
        embed.add_field(name="Account created at", value=str(member.created_at), inline=False)
        
        # Get the current invites for the server
        current_server_invites = await member.guild.invites()
        
        async with aiosqlite.connect(invitelog_database) as con:
            async with con.cursor() as cur:
                # Get all the invites for the server from the database
                await cur.execute("SELECT INVITE_CODE, CURRENT_USES, MAX_USES, INVITER_ID FROM invitelog WHERE SERVER_ID = ?", (member.guild.id,))
                db_invites = await cur.fetchall()
                
                # Find the invite that has one more use than the database
                for invite in current_server_invites:
                    for db_invite in db_invites:
                        if invite.code == db_invite[0] and invite.uses == db_invite[1] + 1:
                            inviter = await self.bot.fetch_user(db_invite[3])
                            expiration_date_unix = invite.expires_at.timestamp()
                            current_uses = invite.uses
                            max_uses = db_invite[2]
                            
                            # Add the new user to the users table
                            await cur.execute("INSERT INTO users (SERVER_ID, INVITE_CODE, USED_BY_NAME, USED_BY_ID) VALUES (?, ?, ?, ?)", (member.guild.id, invite.code, member.name, member.id))
                            
                            # Update the current uses of the invite in the invitelog table
                            await cur.execute("UPDATE invitelog SET CURRENT_USES = ? WHERE SERVER_ID = ? AND INVITE_CODE = ?", (current_uses, member.guild.id, invite.code))
                            
                            await con.commit()
                            now = datetime.datetime.now().timestamp()
                            remaining_time = expiration_date_unix - now if expiration_date_unix != 0 else 0
                            if remaining_time > 0:
                                days, remainder = divmod(remaining_time, 86400)
                                hours, remainder = divmod(remainder, 3600)
                                minutes, seconds = divmod(remainder, 60)
                                expiration_string = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
                            else:
                                expiration_string = "No expiration"
                            
                            # Add invite information to the embed
                            embed.add_field(name="Invite Code", value=invite.code, inline=False)
                            embed.add_field(name="Inviter", value=f"{inviter.name} ID: {inviter.id}", inline=False)
                            embed.add_field(name="Invite Channel", value=f"<#{invite.channel.id}>", inline=False)
                            embed.add_field(name="Invite Expiration", value=f'{expiration_string}', inline=False)
                            embed.add_field(name="Invite Uses", value=f"{current_uses} / {max_uses if max_uses != 0 else 'Infinite'}", inline=False)
                            
                            break
        
        await log_channel.send(embed=embed)
        
        loop = asyncio.get_event_loop()
        self.update_invites_task = loop.create_task(self.update_invites_loop())
    
    @commands.group(name='invite', aliases=['inv'], invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invitelog_base(self, ctx):
        '''
        All commands related to the invite group.
        - `invite list` Displays a list of all the active invites for the current server.
        - `invite show` Displays information about a specific invite.
        - `invite kick` Kicks all users who joined the server using a specific invite.
        '''
        embed = discord.Embed(title='Invitelog usage', description=f'', color=0x00ff00, timestamp=datetime.utcnow())
        embed.set_footer(text=botversion)
        await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
    
    
    @invitelog_base.command(name='list', invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invitelog_list(self, ctx):
        '''
        This command displays a list of all the active invites for the current server.
        
        The invites are displayed in a paginated embed, with 4 invites per page. Users can navigate through the pages using the "◀️" and "▶️" reactions.
        
        Each invite entry in the list includes the following information:
        - Invite code
        - Inviter's name and ID
        - Invite channel
        - Invite expiration date and time (or "No expiration" if the invite doesn't expire)
        - Current uses of the invite / Maximum uses (or "Infinite" if the invite has no use limit)
        '''
        async with aiosqlite.connect(invitelog_database) as con:
            async with con.cursor() as cur:
                # Get all the active invites for the server
                await cur.execute("SELECT INVITE_CODE, CURRENT_USES, MAX_USES, INVITER_ID, INVITER_NAME, INVITE_CHANNEL_ID, EXPIRATION_DATE_UNIX FROM invitelog WHERE SERVER_ID = ?", (ctx.guild.id,))
                invites = await cur.fetchall()
        
        if not invites:
            embed = discord.Embed(title="Invite List", description="There are no active invites for this server.", color=0x00ff00)
            await ctx.send(embed=embed)
            return
        
        invites_per_page = 4
        total_pages = (len(invites) + invites_per_page - 1) // invites_per_page
        
        embeds = []
        for page_num in range(total_pages):
            start_index = page_num * invites_per_page
            end_index = min((page_num + 1) * invites_per_page, len(invites))
            
            embed = discord.Embed(title=f"Invite List - Page {page_num + 1}/{total_pages}", color=0x00ff00)
            for invite in invites[start_index:end_index]:
                invite_code, current_uses, max_uses, inviter_id, inviter_name, invite_channel_id, expiration_date_unix = invite
                inviter = await self.bot.fetch_user(inviter_id)
                
                now = datetime.datetime.now().timestamp()
                remaining_time = expiration_date_unix - now if expiration_date_unix != 0 else 0
                if remaining_time > 0:
                    days, remainder = divmod(remaining_time, 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    expiration_string = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
                else:
                    expiration_string = "No expiration"
                
                embed.add_field(name=f"Invite Code: {invite_code}", value=
                                f"**Inviter:** {inviter.name} (ID: {inviter_id})\n"
                                f"**Invite Channel:** <#{invite_channel_id}>\n"
                                f"**Invite Expiration:** {expiration_string}\n"
                                f"**Invite Uses:** {current_uses} / {max_uses if max_uses != 0 else 'Infinite'}", inline=False)
            embeds.append(embed)
        
        current_page = 0
        message = await ctx.send(embed=embeds[current_page])
        await message.add_reaction("◀️")
        await message.add_reaction(f"{current_page + 1}\uFE0F\u20E3")
        await message.add_reaction("▶️")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]
        
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
                await message.remove_reaction(str(reaction.emoji), user)
                
                if str(reaction.emoji) == "▶️" and current_page < total_pages - 1:
                    await message.remove_reaction(f"{current_page + 1}\uFE0F\u20E3", self.bot.user)
                    current_page += 1
                    await message.edit(embed=embeds[current_page])
                    await message.add_reaction(f"{current_page + 1}\uFE0F\u20E3")
                    
                elif str(reaction.emoji) == "◀️" and current_page > 0:
                    await message.remove_reaction(f"{current_page + 1}\uFE0F\u20E3", self.bot.user)
                    current_page -= 1
                    await message.edit(embed=embeds[current_page])
                    await message.add_reaction(f"{current_page + 1}\uFE0F\u20E3")
                    
            except asyncio.TimeoutError:
                await message.remove_reaction("◀️", self.bot.user)
                await message.remove_reaction("▶️", self.bot.user)
                await message.remove_reaction(f"{current_page + 1}\uFE0F\u20E3", self.bot.user)
                break
    
    @invitelog_base.command(name='show', invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invitelog_show(self, ctx, invite_code:str):
        '''
        This command displays information about a specific invite.
        
        The information displayed includes:
        - Invite code
        - Inviter's name and ID
        - Invite channel
        - Invite expiration date and time (or "No expiration" if the invite doesn't expire)
        - Current uses of the invite / Maximum uses (or "Infinite" if the invite has no use limit)
        - A list of users who joined the server using the invite
        '''
        async with aiosqlite.connect(invitelog_database) as con:
            async with con.cursor() as cur:
                # Get the invite information from the database
                await cur.execute("SELECT INVITE_CODE, CURRENT_USES, MAX_USES, INVITER_ID, INVITER_NAME, INVITE_CHANNEL_ID, EXPIRATION_DATE_UNIX FROM invitelog WHERE INVITE_CODE = ?", (invite_code,))
                invite_info = await cur.fetchone()
                
                if not invite_info:
                    embed = discord.Embed(title="Invite Information", description=f"No invite found with the code '{invite_code}'.", color=0xff0000)
                    await ctx.send(embed=embed)
                    return
                
                invite_code, current_uses, max_uses, inviter_id, inviter_name, invite_channel_id, expiration_date_unix = invite_info
                inviter = await self.bot.fetch_user(inviter_id)
                
                now = datetime.datetime.now().timestamp()
                remaining_time = expiration_date_unix - now if expiration_date_unix != 0 else 0
                if remaining_time > 0:
                    days, remainder = divmod(remaining_time, 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    expiration_string = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
                else:
                    expiration_string = "No expiration"
                
                # Get the list of users who joined using this invite
                await cur.execute("SELECT USED_BY_NAME, USED_BY_ID FROM users WHERE SERVER_ID = ? AND INVITE_CODE = ?", (ctx.guild.id, invite_code))
                users = await cur.fetchall()
                
                embed = discord.Embed(title="Invite Information", color=0x00ff00)
                embed.add_field(name="Invite Code", value=invite_code, inline=False)
                embed.add_field(name="Inviter", value=f"{inviter.name} (ID: {inviter_id})", inline=False)
                embed.add_field(name="Invite Channel", value=f"<#{invite_channel_id}>", inline=False)
                embed.add_field(name="Invite Expiration", value=expiration_string, inline=False)
                embed.add_field(name="Invite Uses", value=f"{current_uses} / {max_uses if max_uses != 0 else 'Infinite'}", inline=False)
                
                if users:
                    user_list = "\n".join(f"{user[0]} (ID: {user[1]})" for user in users)
                    embed.add_field(name="Users Joined", value=user_list, inline=False)
                else:
                    embed.add_field(name="Users Joined", value="No users joined using this invite.", inline=False)
                    
                await ctx.send(embed=embed)
    
    @invitelog_base.command(name='kick', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invitelog_kick(self, ctx, invite_code:str):
        '''
        This command kicks all users who joined the server using a specific invite.
        '''
        async with aiosqlite.connect(invitelog_database) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT USED_BY_NAME, USED_BY_ID FROM users WHERE SERVER_ID = ? AND INVITE_CODE = ?", (ctx.guild.id, invite_code))
                users = await cur.fetchall()
                
                if users:
                    kicked_users = []
                    not_kicked_users = []
                    for user in users:
                        user_name, user_id = user
                        member = ctx.guild.get_member(user_id)
                        if member:
                            await member.kick(reason=f"Kicked for joining using the invite code {invite_code}")
                            kicked_users.append(f"{user_name} (ID: {user_id})")
                        else:
                            not_kicked_users.append(f"Unable to kick user {user_name} (ID: {user_id}) as they are no longer in the server.")
                    
                    embed = discord.Embed(title="Invite Kick", color=0x00ff00)
                    if kicked_users:
                        kicked_users_list = "\n".join(kicked_users)
                        embed.add_field(name="Kicked users", value=f"Successfully kicked the following users who joined using the invite code `{invite_code}`:\n\n{kicked_users_list}")
                    
                    elif not_kicked_users:
                        not_kicked_users_list = "\n".join(not_kicked_users)
                        embed.add_field(name="Not kicked users", value=f"Unable to kick the following users with invite:`{invite_code}` as they are no longer in the server.\n\n{not_kicked_users_list}.")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Invite Kick", description=f"No users found who joined using the invite code `{invite_code}`.", color=0xff0000)
                    await ctx.send(embed=embed)
    
    async def cog_unload(self):
        # print('invitelog cog_unload stopping update_invites_loop loop')
        if self.update_invites_task and not self.update_invites_task.done():
            self.update_invites_task.cancel()
    
    async def cog_load(self):
        await asyncio.sleep(2)
        # print('invitelog cog_load starting update_invites_loop loop')
        if self.update_invites_task and self.update_invites_task.done():
            loop = asyncio.get_event_loop()
            self.update_invites_task = loop.create_task(self.update_invites_loop())
            await self.update_invites()
    
    @commands.Cog.listener()
    async def on_disconnect(self):
        if self.update_invites_task and not self.update_invites_task.done():
            self.update_invites_task.cancel()
    
    @commands.Cog.listener()
    async def on_resumed(self):
        await asyncio.sleep(2)
        if self.update_invites_task and self.update_invites_task.done():
            loop = asyncio.get_event_loop()
            self.update_invites_task = loop.create_task(self.update_invites_loop())
            await self.update_invites()
    
    async def update_invites_loop(self):
        while True:
            await asyncio.sleep(SECOND_LOOP_DELAY)
            # print ('update_invites_loop')
            await self.update_invites()

async def setup(bot):
    await bot.add_cog(Invitelog(bot))