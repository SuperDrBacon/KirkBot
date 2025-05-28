import os
import sqlite3
from datetime import datetime

import requests
from discord.ext import commands

from cogs.utils.constants import COMMAND_LOGS_DATABASE


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print('Command logging system online')
        
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Event listener that logs every command execution"""
        try:
            raw_message = ctx.message.content
            command_name = ctx.command.qualified_name
            words = raw_message.split()
            command_parts = command_name.split()
            
            # Check if we need to extract subcommands from the message
            if len(command_parts) > 1:
                # Skip the first word (the command with prefix)
                current_position = 1
                
                # Skip over each subcommand in the message
                for i in range(1, len(command_parts)):
                    # If we've reached the end of the words, break
                    if current_position >= len(words):
                        break
                    
                    # If the current word matches the subcommand, move to the next word
                    if words[current_position].lower() == command_parts[i].lower():
                        current_position += 1
                
                # Arguments are everything after the last matched subcommand
                if current_position < len(words):
                    args = ' '.join(words[current_position:])
                else:
                    args = ""
            else:
                # Simple command (no subcommands)
                if len(words) > 1:
                    args = ' '.join(words[1:])
                else:
                    args = ""
            
            # Get user and context info
            username = ctx.author.name
            user_id = ctx.author.id
            server_name = ctx.guild.name if ctx.guild else "DM"
            server_id = ctx.guild.id if ctx.guild else None
            channel_name = ctx.channel.name if hasattr(ctx.channel, 'name') else "DM"
            channel_id = ctx.channel.id
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Log to database
            con = sqlite3.connect(COMMAND_LOGS_DATABASE)
            cur = con.cursor()
            
            cur.execute('''
                INSERT INTO command_logs(
                    command_name,
                    args,
                    username,
                    user_id,
                    server_name, 
                    server_id, 
                    channel_name, 
                    channel_id, 
                    timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                (command_name, 
                args,
                username,
                user_id,
                server_name,
                server_id, 
                channel_name,
                channel_id, 
                timestamp))
            
            con.commit()
            con.close()
            
            # Notify admin portal
            admin_portal_url = "http://localhost:5005/api/new_command"
            command_data = {
                "command_name": command_name,
                "args": args,
                "username": username,
                "server_name": server_name,
                "channel_name": channel_name,
                "timestamp": timestamp
            }
            
            try:
                requests.post(admin_portal_url, json=command_data, timeout=0.5)
            except requests.RequestException:
                # Silently fail if admin portal isn't running
                pass
                
        except Exception as e:
            print(f"Error logging command: {e}")

async def setup(bot):
    await bot.add_cog(Log(bot))

