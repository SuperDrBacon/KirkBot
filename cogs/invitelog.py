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
config = ConfigParser()
config.read(rf'{ospath}/config.ini')

prefix = config['BOTCONFIG']['prefix']
invitelog_database = rf'{ospath}/cogs/invitelog_data.db'

SECOND_LOOP_DELAY = 5

class InviteLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_invites_task = None
        if not self.update_invites_task or self.update_invites_task.done():
            self.update_invites_task = asyncio.create_task(self.update_invites_loop())
        functions.checkForFile(filepath=os.path.dirname(invitelog_database), filename=os.path.basename(invitelog_database), database=True, dbtype='invitelog')
    
    @commands.Cog.listener()
    async def on_ready(self):
        # await self.update_invites_loop()
        # await self.update_invites()
        print('InviteLog module is online')
    
    async def update_invites(self):
        async with aiosqlite.connect(invitelog_database) as con:
            async with con.cursor() as c:
                # Loop through each server
                for server in self.bot.guilds:
                    # Get the current invites for the server
                    invites = await server.invites()
                    
                    # Update the database with the new invite information
                    for invite in invites:
                        await c.execute("SELECT * FROM invitelog WHERE SERVER_ID = ? AND INVITE_CODE = ?", (server.id, invite.code))
                        existing_invite = await c.fetchone()
                        if existing_invite:
                            # Update the existing invite
                            await c.execute("UPDATE invitelog SET CURRENT_USES = ? WHERE SERVER_ID = ? AND INVITE_CODE = ?;",
                                        (invite.uses, server.id, invite.code))
                        else:
                            # Add a new invite
                            await c.execute("INSERT INTO invitelog(SERVER_ID, INVITE_CODE, CURRENT_USES, MAX_USES, INVITER_ID, INVITER_NAME, INVITE_CHANNEL_ID, EXPIRATION_DATE_UNIX) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                                        (server.id, invite.code, invite.uses, invite.max_uses, invite.inviter.id, invite.inviter.name, invite.channel.id, (invite.expires_at.timestamp() if invite.expires_at else 0)))
                    
                    # Remove any invites that are no longer active
                    await c.execute("SELECT INVITE_CODE FROM invitelog WHERE SERVER_ID = ?", (server.id,))
                    db_invites = [row[0] for row in await c.fetchall()]
                    for db_invite in db_invites:
                        if db_invite not in [invite.code for invite in invites]:
                            await c.execute("DELETE FROM invitelog WHERE SERVER_ID = ? AND INVITE_CODE = ?", (server.id, db_invite))
                            # await c.execute("DELETE FROM users WHERE INVITE_CODE = ?", (db_invite,)) # dont remove the users from the users table as this is a log of all users that have joined a server
                # else:
                #     # The server is no longer available, remove it from the database
                #     await c.execute("DELETE FROM invitelog WHERE SERVER_ID = ?", (server.id,))
                #     # await c.execute("DELETE FROM users WHERE INVITE_CODE IN (SELECT INVITE_CODE FROM invitelog WHERE SERVER_ID = ?)", (server_id,)) # dont remove the users from the users table as this is a log of all users that have joined a server
            
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
            async with con.cursor() as c:
                # Get all the invites for the server from the database
                await c.execute("SELECT INVITE_CODE, CURRENT_USES, MAX_USES, INVITER_ID FROM invitelog WHERE SERVER_ID = ?", (member.guild.id,))
                db_invites = await c.fetchall()
                
                # Find the invite that has one more use than the database
                for invite in current_server_invites:
                    for db_invite in db_invites:
                        if invite.code == db_invite[0] and invite.uses == db_invite[1] + 1:
                            inviter = await self.bot.fetch_user(db_invite[3])
                            expiration_date_unix = invite.expires_at.timestamp()
                            current_uses = invite.uses
                            max_uses = db_invite[2]
                            
                            # Add the new user to the users table
                            await c.execute("INSERT INTO users (SERVER_ID, INVITE_CODE, USED_BY_NAME, USED_BY_ID) VALUES (?, ?, ?, ?)", (member.guild.id, invite.code, member.name, member.id))
                            
                            # Update the current uses of the invite in the invitelog table
                            await c.execute("UPDATE invitelog SET CURRENT_USES = ? WHERE SERVER_ID = ? AND INVITE_CODE = ?", (current_uses, member.guild.id, invite.code))
                            
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
                            embed.add_field(name="Invite Uses", value=f"{current_uses} / {max_uses if not 0 else 'infinite'}", inline=False)
                            
                            break
        
        await log_channel.send(embed=embed)
        
        loop = asyncio.get_event_loop()
        self.update_invites_task = loop.create_task(self.update_invites_loop())
    
    @commands.command(aliases=["invs", "invites", "invites_list", "invitelist", "invlist", "inviteslist"])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invite_list(self, ctx):
        async with aiosqlite.connect(invitelog_database) as con:
            async with con.cursor() as c:
                # Get all the active invites for the server
                await c.execute("SELECT INVITE_CODE, CURRENT_USES, MAX_USES, INVITER_ID, INVITER_NAME, INVITE_CHANNEL_ID, EXPIRATION_DATE_UNIX FROM invitelog WHERE SERVER_ID = ?", (ctx.guild.id,))
                invites = await c.fetchall()
        
        if not invites:
            embed = discord.Embed(title="Invite List", description="There are no active invites for this server.", color=0x00ff00)
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(title="Invite List", color=0x00ff00)
        
        for invite in invites:
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
            # self.loopcounter += SECOND_LOOP_DELAY
            await self.update_invites()

async def setup(bot):
    await bot.add_cog(InviteLog(bot))