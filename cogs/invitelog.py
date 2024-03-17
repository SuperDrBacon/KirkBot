import asyncio
import os
import discord

from configparser import ConfigParser
from discord import Embed
from discord.ext import commands, tasks

path = os.path.abspath(os.getcwd())
config = ConfigParser()
config.read(rf'{path}/config.ini')

prefix = config['BOTCONFIG']['prefix']


class InviteLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.load_invites()
    
    async def load_invites(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            self.invites[guild.id] = await guild.invites()
    
    def find_invite_by_code(self, inv_list, code):
        for inv in inv_list:
            if inv.code == code:
                return inv
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        
        log_channel_id = 1153340486661185580  # glowing invites channel
        log_channel = self.bot.get_channel(log_channel_id)
        
        embed = discord.Embed(title="New member joined", color=0x00ff00)
        embed.add_field(name="Member", value=f"{member.mention} (ID: {member.id})", inline=False)
        embed.add_field(name="Account created at", value=str(member.created_at), inline=False)
        
        invites_before = self.invites[member.guild.id]
        invites_after = await member.guild.invites()
        self.invites[member.guild.id] = invites_after
        
        for invite in invites_before:
            if invite.uses < self.find_invite_by_code(invites_after, invite.code).uses:        
                embed.add_field(name="Invite code", value=invite.code, inline=False)
                embed.add_field(name="Inviter", value=invite.inviter.name, inline=False)
                embed.add_field(name="Invite channel", value=invite.channel.mention, inline=False)
                embed.add_field(name="Invite created at", value=str(invite.created_at), inline=False)
                embed.add_field(name="Invite uses", value=str(invite.uses), inline=False)
        
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InviteLog(bot))