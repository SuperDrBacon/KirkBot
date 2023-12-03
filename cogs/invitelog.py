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
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Fetch the current invite list from the guild and store it in a dictionary.
        invites_before_join = {invite.code: invite for invite in await member.guild.invites()}
        
        # Wait for a few seconds, then fetch the invite list again.
        await asyncio.sleep(2)  # Wait for the on_member_join event to finish.
        invites_after_join = {invite.code: invite for invite in await member.guild.invites()}
        
        # Find the invite which was used by comparing the 'uses' field.
        used_invite = None
        for invite in invites_after_join.values():
            if invite.uses > invites_before_join[invite.code].uses:
                used_invite = invite
                break
        
        if used_invite is None:
            return
        
        # Now we have the invite that was used, and can extract information from it.
        inviter = used_invite.inviter
        invite_channel = used_invite.channel
        
        # Send a message to a specific channel.
        log_channel_id = 1153340486661185580  # Replace with your channel ID.
        log_channel = self.bot.get_channel(log_channel_id)
        
        # Create an embed message.
        embed = discord.Embed(title="New member joined", color=0x00ff00)
        embed.add_field(name="Member", value=f"{member.mention} (ID: {member.id})", inline=False)
        embed.add_field(name="Account created at", value=str(member.created_at), inline=False)
        embed.add_field(name="Invite code", value=used_invite.code, inline=False)
        embed.add_field(name="Inviter", value=inviter.name, inline=False)
        embed.add_field(name="Invite channel", value=invite_channel.mention, inline=False)
        embed.add_field(name="Invite created at", value=str(used_invite.created_at), inline=False)
        embed.add_field(name="Invite uses", value=str(used_invite.uses), inline=False)
        
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InviteLog(bot))