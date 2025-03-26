import asyncio
import sqlite3
import time
import uuid
import discord
import requests

from discord.ext import commands
from datetime import datetime, timezone
from io import BytesIO
from zipfile import ZipFile
from cogs.utils.constants import ADMIN_PORTAL_WS_URL, ARCHIVE_DATABASE

class Archiver(commands.Cog):
    '''
    This module is used to keep track off all messages sent in a server to use them in the ai module.
    '''
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Archiver module online')

    # Helper method to notify admin portal of new messages
    def notify_admin_portal(self, ctx, message_data):
        try:
            # Make sure server_id is included in the notification
            if hasattr(ctx, 'guild') and ctx.guild:
                message_data['server_id'] = ctx.guild.id
                message_data['server_name'] = ctx.guild.name
                
            requests.post(ADMIN_PORTAL_WS_URL, json=message_data, timeout=0.5)
        except requests.RequestException:
            # Silently fail if admin portal isn't running
            pass

    @commands.Cog.listener()
    async def on_message(self, ctx):
        server_name = ctx.guild.name
        server_id= ctx.guild.id
        channel_name = ctx.channel.name
        channel_id = ctx.channel.id
        user_name = ctx.author.name
        user_id = ctx.author.id
        message = ctx.content
        message_id = ctx.id
        reply = 0
        now_utc = str(datetime.now(timezone.utc))
        now_unix = str(time.time())
        
        if ctx.reference:
            reply = 1
            print(f'#{channel_name[:15]:<15} ╔═══ {ctx.reference.resolved.author.name}: {ctx.reference.resolved.content}')
            original_username = ctx.reference.resolved.author.name
            original_username_id = ctx.reference.resolved.author.id
            original_message = ctx.reference.resolved.content
            original_message_id = ctx.reference.resolved.id
        
        try:
            if message == "":
                message = ctx.attachments[0].url
        except Exception:
            try:
                message = ctx.attachments[0].proxy_url
            except Exception:
                return
        
        print(f'#{channel_name[:15]:<15} - {user_name}: {message}')
        
        # Prepare message data for dashboard notification
        message_data = {
            "server_name": server_name,
            "channel_name": channel_name,
            "username": user_name,
            "message": message,
            "is_reply": reply
        }
        
        if reply == 1:
            message_data["original_username"] = original_username
            message_data["original_message"] = original_message
            
            try:
                con = sqlite3.connect(ARCHIVE_DATABASE)
                cur = con.cursor()
                data_to_insert = '''INSERT INTO archive_data(
                            SERVER_NAME,
                            SERVER_ID,
                            CHANNEL_NAME,
                            CHANNEL_ID,
                            USERNAME,
                            USER_ID,
                            MESSAGE,
                            MESSAGE_ID,
                            IS_REPLY,
                            ORIGINAL_USERNAME,
                            ORIGINAL_USER_ID,
                            ORIGINAL_MESSAGE,
                            ORIGINAL_MESSAGE_ID,
                            DATE_TIME,
                            UNIX_TIME) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'''
                data_tuple = (
                            server_name, 
                            server_id, 
                            channel_name, 
                            channel_id, 
                            user_name, 
                            user_id, 
                            message, 
                            message_id, 
                            reply, 
                            original_username, 
                            original_username_id, 
                            original_message, 
                            original_message_id, 
                            now_utc,
                            now_unix)
                cur.execute(data_to_insert, data_tuple)
                con.commit()
            
            except Exception as error:
                print("Failed to insert multiple records into sqlite table:", error)
            finally:
                if con:
                    cur.close()
                    con.close()
            
            # Notify admin portal of new message
            self.notify_admin_portal(ctx, message_data)
        else:
            try:
                con = sqlite3.connect(ARCHIVE_DATABASE)
                cur = con.cursor()
                data_to_insert = '''INSERT INTO archive_data(
                            SERVER_NAME,
                            SERVER_ID,
                            CHANNEL_NAME,
                            CHANNEL_ID,
                            USERNAME,
                            USER_ID,
                            MESSAGE,
                            MESSAGE_ID,
                            IS_REPLY,
                            DATE_TIME,
                            UNIX_TIME) VALUES (?,?,?,?,?,?,?,?,?,?,?);'''
                data_tuple = (
                            server_name, 
                            server_id, 
                            channel_name, 
                            channel_id, 
                            user_name, 
                            user_id, 
                            message, 
                            message_id, 
                            reply, 
                            now_utc,
                            now_unix)
                cur.execute(data_to_insert, data_tuple)
                con.commit()
            
            except Exception as error:
                print("Failed to insert multiple records into sqlite table:", error)
            finally:
                if con:
                    cur.close()
                    con.close()
            
            # Notify admin portal of new message
            self.notify_admin_portal(ctx, message_data)
    
    @commands.command(name='archive', hidden=True)
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def archive_channel(self, ctx, number:int=None):
        '''
        Gets all the messages and files in the channel and puts them in a file named the channel name.
        '''
        channel_name = ctx.channel.name
        uuuid = f'-{str(uuid.uuid4())[:3]}-'
        text_content = ""
        archive_content = []
        messages = [message async for message in ctx.channel.history(limit=number, oldest_first=True)]
        
        await ctx.send(f'Archiving {len(messages)} messages in {channel_name}')
        
        for message in messages:
            content = f"{message.author.name}: {message.content}\n"
            text_content += content
            if message.attachments:
                for attachment in message.attachments:
                    response = await attachment.read()
                    try:
                        file_data = BytesIO(response)
                        archive_content.append((attachment.filename, file_data.getvalue()))
                    except Exception as e:
                        print(f"Failed to process attachment: {attachment.filename}. Error: {str(e)}")
                        continue
        
        zip_files = []
        zip_size = 0
        
        def create_new_zip(include_text_file=True):
            zip_file = BytesIO()  # Create a new zip_file object
            with ZipFile(zip_file, 'w') as zip_obj:
                if include_text_file:
                    text_file = BytesIO(text_content.encode('utf-8'))
                    zip_obj.writestr(f'{channel_name}_messages.txt', text_file.getvalue())
            zip_files.append(zip_file)
        
        create_new_zip()
        
        for filename, data in archive_content:
            if zip_size + len(data) > 25 * 1024 * 1024:
                create_new_zip(include_text_file=False)
                zip_size = 0
            
            current_zip = zip_files[-1]  # Get the last created zip_file object
            with ZipFile(current_zip, 'a') as zip_obj:
                zip_obj.writestr(filename, data)
            zip_size += len(data)
        
        for i, zip_data in enumerate(zip_files):
            zip_data.seek(0)
            filename = f'{channel_name}_archive{uuuid}_part{i+1}.zip'
            try:
                await ctx.send(file=discord.File(zip_data, filename=filename))
                await asyncio.sleep(1)
            except discord.errors.HTTPException:
                await ctx.send(f"Part {i+1} of the ZIP file did not send for some reason.")
                await asyncio.sleep(1)
    
    @commands.command(name='count', hidden=True)
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def count(self, ctx, number:int=None):
        '''
        Counts the number of messages in the channel.
        '''
        messages = [message async for message in ctx.channel.history(limit=number, oldest_first=True)]
        await ctx.send(f'There are {len(messages)} messages in {ctx.channel.name}', delete_after=5)
        await ctx.message.delete(delay=5)
    
    @commands.command(name='getuserlist', hidden=True)
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def getuserlist(self, ctx, serverid:int):
        con = sqlite3.connect(ARCHIVE_DATABASE)
        cur = con.cursor()
        
        cur.execute(f"SELECT USER_ID, USERNAME FROM archive_data WHERE SERVER_ID = ?", (serverid,))
        userdata = cur.fetchall()
        previous_usernames = {}
        file_data = BytesIO()
        
        for user in userdata:
            userid, username = user
            print(userid, username)
            if userid in previous_usernames:
                previous_names = previous_usernames[userid]
            else:
                previous_names = []
            getuser = await self.bot.fetch_user(userid)
            
            if getuser is not None:
                user_info = f'{userid} - {getuser.name}#{getuser.discriminator} - previous names: {", ".join(previous_names)}'
                previous_names.append(getuser.name)  # Add the current name to previous names
                previous_usernames[userid] = previous_names
            else:
                user_info = f'{userid} - {username} - previous names: {", ".join(previous_names)}'
            
            file_data.write(user_info.encode('utf-8'))
        file_data.seek(0)
        print('done making file')
        await ctx.send(file=discord.File(file_data, filename="userlist.txt"))
        print ('done sending file')



async def setup(bot):
    await bot.add_cog(Archiver(bot))