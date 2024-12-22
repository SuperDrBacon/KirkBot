import asyncio
import os
import re
from datetime import datetime, timedelta, timezone
from configparser import ConfigParser

# import sqlite3
import aiosqlite
import discord
from discord.ext import commands, tasks

import cogs.utils.functions as functions

ospath = os.path.abspath(os.getcwd())
archive_database = rf'{ospath}/cogs/archive_data.db'
autodelete_database = rf'{ospath}/cogs/autodelete_data.db'
config, info = ConfigParser(), ConfigParser()
info.read(rf'{ospath}/info.ini')
config.read(rf'{ospath}/config.ini')
command_prefix = config['BOTCONFIG']['prefix']
botversion = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']

MSG_DEL_DELAY = 10
SECOND_LOOP_DELAY = 5

TIME_UNITS = {  
    's':        ('second',  'seconds',  1),
    'sec':      ('second',  'seconds',  1),
    'secs':     ('second',  'seconds',  1),
    'second':   ('second',  'seconds',  1),
    'seconds':  ('second',  'seconds',  1),
    'm':        ('minute',  'minutes',  60),
    'min':      ('minute',  'minutes',  60),
    'mins':     ('minute',  'minutes',  60),
    'minute':   ('minute',  'minutes',  60),
    'minutes':  ('minute',  'minutes',  60),
    'h':        ('hour',    'hours',    3600),
    'hr':       ('hour',    'hours',    3600),
    'hrs':      ('hour',    'hours',    3600),
    'hour':     ('hour',    'hours',    3600),
    'hours':    ('hour',    'hours',    3600),
    'd':        ('day',     'days',     86400),
    'day':      ('day',     'days',     86400),
    'days':     ('day',     'days',     86400),
    'w':        ('week',    'weeks',    604800),
    'week':     ('week',    'weeks',    604800),
    'weeks':    ('week',    'weeks',    604800),
    'month':    ('month',   'months',   2592000),
    'months':   ('month',   'months',   2592000)}

class Autodelete(commands.Cog):
    '''
    The autodelete module contains all commands related to the autodelete feature.
    '''
    def __init__(self, bot):
        self.bot = bot
        self.loopcounter = 0
        self.monitor_expired_messages_task = None
        functions.checkForFile(filepath=os.path.dirname(autodelete_database), filename=os.path.basename(autodelete_database), database=True, dbtype='autodelete')
    
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.monitor_expired_messages_task or self.monitor_expired_messages_task.done():
            self.monitor_expired_messages_task = asyncio.create_task(self.monitor_expired_messages_loop())
        await self.fetch_missed_messages()
        print('Autodelete module online')
    
    async def time_seconds(self, numeric_part:int, unit_part:str):
        seconds = numeric_part * TIME_UNITS[unit_part][2]
        return int(seconds)
    
    async def fetch_missed_messages(self):
        async with aiosqlite.connect(autodelete_database) as con:
            async with con.execute("SELECT server_id, channel_id FROM channels") as cursor:
                server_channels = await cursor.fetchall()
            
            for server_id, channel_id in server_channels:
                guild = self.bot.get_guild(server_id)
                if guild:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        try:
                            async with con.execute("SELECT message_time FROM messages WHERE channel_id = ? ORDER BY message_time ASC LIMIT 1", (channel.id, )) as cursor:
                                oldest_message_time = await cursor.fetchone()
                            
                            if oldest_message_time:
                                oldest_message_time = oldest_message_time[0]
                                before = datetime.fromtimestamp(oldest_message_time)
                            else:
                                before = None
                            
                            channel_messages = [message async for message in channel.history(limit=None, oldest_first=True, before=before) if not message.pinned]
                            
                            for message in channel_messages:
                                await con.execute("INSERT OR IGNORE INTO messages (SERVER_ID, CHANNEL_ID, MESSAGE_ID, MESSAGE_TIME) VALUES (?, ?, ?, ?);", (guild.id, channel.id, message.id, functions.get_unix_time()))
                            await con.commit()
                        
                        except discord.Forbidden:
                            await channel.send(f"Permission denied for deleting messages. Please give me the permission to delete messages in this channel.{channel.mention}")
                        
                        except (aiosqlite.DatabaseError, aiosqlite.IntegrityError, aiosqlite.ProgrammingError, aiosqlite.OperationalError, aiosqlite.NotSupportedError) as e:
                            print(f"Something went wrong with the database. Please try again later. Error: {type(e).__name__} - {e} - {e.args}")
                    else:
                        await self.remove_deleted_item(server=False, channel=True, message=False, server_id=None, channel_id=channel_id, message_id=None)
                else:
                    await self.remove_deleted_item(server=True, channel=False, message=False, server_id=server_id, channel_id=None, message_id=None)
    
    async def delete_before_command_start(self, ctx, time:int=None, count:int=None):
        time_limit = discord.utils.utcnow() - timedelta(days=13.9)  # 14 days, plus margin of error
        full_message_list = [message async for message in ctx.channel.history(limit=None, before=ctx.message.created_at, oldest_first=True) if not message.pinned]
        messages_to_delete = []
        messages_to_database = []
        if time and count:
            messages_to_delete = full_message_list[:count]
            messages_to_database = full_message_list[count:]
        elif time:
            for message in full_message_list:
                if message.created_at < ctx.message.created_at - timedelta(seconds=time):
                    messages_to_delete.append(message)
                else:
                    messages_to_database.append(message)
        elif count:
            messages_to_delete = full_message_list[:count]
            messages_to_database = full_message_list[count:]
        
        if messages_to_database:
            print('Inserting messages to database in delete_before_command_start function')
            try:
                async with aiosqlite.connect(autodelete_database) as con:
                    data_to_insert = [(ctx.guild.id, ctx.channel.id, message.id, functions.get_unix_time()) for message in messages_to_database]
                    print(f'Length of data_to_insert: {len(data_to_insert)}')
                    
                    # Split data_to_insert into chunks of size 500
                    chunks = [data_to_insert[i:i + 500] for i in range(0, len(data_to_insert), 500)]
                    print(f'Length of chunks: {len(chunks)}')
                    
                    for chunk in chunks:
                        await con.executemany("INSERT INTO messages (SERVER_ID, CHANNEL_ID, MESSAGE_ID, MESSAGE_TIME) VALUES (?, ?, ?, ?);", chunk)
                    
                    await con.commit()
            except Exception as e:
                print(f'Error in delete_before_command_start, inserting messages to database: \n\n {e} \n\n')
        
        if messages_to_delete:
            bulk_deletable = []
            non_bulk_deletable = []
            for msg in messages_to_delete:
                if msg.created_at > time_limit:
                    bulk_deletable.append(msg)
                else:
                    non_bulk_deletable.append(msg)
            
            # Bulk delete messages
            for i in range(0, len(bulk_deletable), 100):  # 100 messages per request
                await ctx.channel.purge(limit=None, bulk=True, check=lambda message: message in bulk_deletable[i:i+100], reason="David Marcus II Autodelete")
                await asyncio.sleep(1)  # Wait for 1 second to avoid rate limit
            
            # Non-bulk delete messages
            for i in range(0, len(non_bulk_deletable), 5):  # 5 messages per request
                await ctx.channel.purge(limit=None, bulk=False, check=lambda message: message in non_bulk_deletable[i:i+5], reason="David Marcus II Autodelete")
                await asyncio.sleep(1)  # Wait for 1 second to avoid rate limit
    
    async def remove_deleted_item(self, server:bool=False, channel:bool=False, message:bool=False, server_id:int=None, channel_id:int=None, message_id:int=None):
        async with aiosqlite.connect(autodelete_database) as con:
            await con.execute("PRAGMA foreign_keys = ON")
            
            # #servers
            if server:
                await con.execute("DELETE FROM servers WHERE server_id = ?", (server_id,))
            
            # #channels
            if channel:
                await con.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
            
            #massages
            if message:
                await con.execute("DELETE FROM messages WHERE MESSAGE_ID = ?", (message_id,))
            
            await con.commit()
    
    async def delete_expired_messages(self, expired_messages):
        for channel_id, message_id, _ in expired_messages:
            try:
                channel = self.bot.get_channel(channel_id)
            except (discord.NotFound, discord.Forbidden) as e:
                if isinstance(e, discord.Forbidden):
                    await channel.send(f"Permission denied to look up channel. Please give me the permission to look at channels.")
                if isinstance(e, discord.NotFound):
                    await self.remove_deleted_item(server=False, channel=True, message=False, server_id=None, channel_id=channel_id, message_id=None)
            
            try:
                message = await channel.fetch_message(message_id)
                if not message.pinned:
                    await message.delete()
                await self.remove_deleted_item(server=False, channel=False, message=True, server_id=None, channel_id=None, message_id=message_id)
            
            except (discord.NotFound, discord.Forbidden) as e:
                if isinstance(e, discord.Forbidden):
                    await channel.send(f"Permission denied for deleting messages. Please give me the permission to delete messages in this channel. {channel.mention}")
                await self.remove_deleted_item(server=False, channel=False, message=True, server_id=None, channel_id=None, message_id=message_id)
                continue
            
            except discord.HTTPException as e:
                if e.response.status == 429:
                    print(f'Rate limit error in delete_expired_messages: \n\n {e} \n\n')
                    await asyncio.sleep(0.2)
                    if not message.pinned:
                        await message.delete()
                    await self.remove_deleted_item(server=False, channel=False, message=True, server_id=None, channel_id=None, message_id=message_id)
                else:
                    print(f'HTTP error in delete_expired_messages: \n\n {e} \n\n')
                continue
    
    async def get_expired_messages(self):
        current_time = functions.get_unix_time()
        expired_messages = []
        async with aiosqlite.connect(autodelete_database) as con:
            async with con.execute("SELECT channel_id, del_after_time, del_after_count FROM channels") as cursor:
                channels_time_count = await cursor.fetchall()
            
            for channel_id, del_after_time, del_after_count in channels_time_count:
                if del_after_time:
                    async with con.execute("SELECT channel_id, message_id, message_time FROM messages WHERE channel_id = ? AND message_time <= ?", (channel_id, current_time - del_after_time)) as cursor:
                        expired_messages += await cursor.fetchall()
                
                if del_after_count:
                    async with con.execute("SELECT channel_id, message_id, message_time FROM messages WHERE channel_id = ? ORDER BY message_time ASC", (channel_id,)) as cursor:
                        possibly_expired_messages = await cursor.fetchall()
                        
                        # print(f'possibly_expired_messages: {len(possibly_expired_messages)}')
                        if len(possibly_expired_messages) > del_after_count:
                            expired_messages += possibly_expired_messages[:len(possibly_expired_messages) - del_after_count]
                            # print(f'expired_messages: {len(expired_messages)}')
            
            if expired_messages:
                # print(f'{expired_messages}')
                await self.delete_expired_messages(expired_messages)
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if not ctx.pinned:
            server_id = ctx.guild.id
            channel_id = ctx.channel.id
            message_id = ctx.id
            current_time = functions.get_unix_time()
            
            async with aiosqlite.connect(autodelete_database) as con:
                async with con.execute("SELECT channel_id FROM channels WHERE channel_id = ?", (channel_id,)) as cursor:
                    channel_in_database = await cursor.fetchone()
                
                if channel_in_database:
                    await con.execute("INSERT INTO messages (SERVER_ID, CHANNEL_ID, MESSAGE_ID, MESSAGE_TIME) VALUES (?, ?, ?, ?);", (server_id, channel_id, message_id, current_time))
                    await con.commit()
    
    @commands.group(name='autodelete', aliases=['ad'], description='All commands related to autodelete', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def autodelete_base(self, ctx):
        '''
        To see a more detailed description of all the autodelte commands use\n
        `help autodelete <command>`
        
        '''
        embed = discord.Embed(title='Autodelete usage', description=f'To see how to start the autodelete module use:\n`{command_prefix}help autodelete start`\n\n\
            To see how to stop the autodelete module use:\n`{command_prefix}help autodelete stop`\n\n\
            To see all the channels the autodelete module is active in use:\n`{command_prefix}help autodelete list`', color=0x00ff00, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=botversion)
        await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
    
    @autodelete_base.command(name='start')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def autodelete_start(self, ctx, *count_and_or_time):
        '''
        Use the following format for time:
        `autodelete start <[count] [time]>`
        If `[count]` is set, messages are deleted after this amount of messages.
        If `[time]` is set, messages are deleted after this amount of time.
        If both `[count]` and `[time]` are set, messages are deleted after which ever one comes first.
        At least one of `[count]` or `[time]` must be set.
        The order of `[count]` and `[time]` does not matter.
        
        Examples:
        `autodelete start 1000 3h`
        `autodelete start 3h 1000`
        `autodelete start 1000`
        `autodelete start 3h`
        
        Valid time formats are:
        `s, sec, secs, second, seconds`
        `m, min, mins, minute, minutes`
        `h, hr, hrs, hour, hours`
        `d, day, days`
        `w, week, weeks`
        `month, months`
        '''
        ctx._wrong_start_format_ = False
        ctx._error_reason_ = ''
        index_count = 0
        index_time = 0
        server_id = ctx.guild.id
        channel_id = ctx.channel.id
        await ctx.message.delete(delay=MSG_DEL_DELAY)
        time_formats = '|'.join(TIME_UNITS.keys())
        for arg in count_and_or_time:
            match = re.match(rf'(^\d+)({time_formats})$', arg, re.IGNORECASE)
            if arg.isdigit():
                index_count += 1
                count = int(arg)
            elif match:
                index_time += 1
                numeric_part = int(match.group(1))
                unit_part = str(match.group(2))
                seconds = await self.time_seconds(numeric_part, unit_part)
                singular_unit_name, plural_unit_name, _ = TIME_UNITS[unit_part]
                unit_name = singular_unit_name if numeric_part == 1 else plural_unit_name
            else:
                ctx._wrong_start_format_ = True
                ctx._error_reason_ = 'Wrong format for start command arguments'
                raise commands.UserInputError
        
        if index_time == 0 and index_count == 1:
            try:
                #only remove by message count in channel
                async with aiosqlite.connect(autodelete_database) as con:
                    async with con.execute("SELECT server_id FROM servers WHERE server_id = ?", (server_id,)) as cursor:
                        existing_server = await cursor.fetchone()
                    if existing_server:
                        await con.execute("INSERT INTO channels (SERVER_ID, CHANNEL_ID, DEL_AFTER_TIME, DEL_AFTER_COUNT) VALUES (?, ?, ?, ?)", (server_id, channel_id, None, count))
                    else:
                        await con.execute("INSERT INTO servers (SERVER_ID) VALUES (?)", (server_id,))
                        await con.execute("INSERT INTO channels (SERVER_ID, CHANNEL_ID, DEL_AFTER_TIME, DEL_AFTER_COUNT) VALUES (?, ?, ?, ?)", (server_id, channel_id, None, count))
                    await con.commit()
                
                embed = discord.Embed(title='Autodelete preparing channel', description=f'Autodelete has been started in {ctx.channel.mention} and will delete all previous messages.', color=0xFF7518, timestamp=datetime.now(timezone.utc))
                embed.set_footer(text=botversion)
                msg = await ctx.send(embed=embed)
                await msg.add_reaction("🔄")
                
                #This can take a while
                try:
                    await self.delete_before_command_start(ctx, time=None, count=count)
                except Exception as e:
                    print(f'Error in delete_before_command_start, count: \n\n {e} \n\n')
                
                get_channel = self.bot.get_channel(channel_id)
                done_embed = discord.Embed(title='Autodelete started', description=f'Autodelete has been started in {get_channel.mention} and will delete messages after {count} messages.', color=0x00ff00, timestamp=datetime.now(timezone.utc))
                done_embed.set_footer(text=botversion)
                msg1 = await get_channel.send(embed=done_embed)
                await msg1.add_reaction("✅")
            
            except aiosqlite.Error as e:
                embed = discord.Embed(title='Autodelete already running', description=f'Autodelete is already running in {ctx.channel.mention}.\n\nTo change autodelete settings the current autodelete needs to be stopped and a new one needs to be started', color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.set_footer(text=botversion)
                await ctx.send(embed=embed, mention_author=False)
                print(f'Error in autodelete startup count: \n\n {e} \n\n')
        
        elif index_time == 1 and index_count == 0:
            try:
                #only remove by time in channel
                async with aiosqlite.connect(autodelete_database) as con:
                    async with con.execute("SELECT server_id FROM servers WHERE server_id = ?", (server_id,)) as cursor:
                        existing_server = await cursor.fetchone()
                    if existing_server:
                        await con.execute("INSERT INTO channels (SERVER_ID, CHANNEL_ID, DEL_AFTER_TIME, DEL_AFTER_COUNT) VALUES (?, ?, ?, ?)", (server_id, channel_id, seconds, None))
                    else:
                        await con.execute("INSERT INTO servers (SERVER_ID) VALUES (?)", (server_id,))
                        await con.execute("INSERT INTO channels (SERVER_ID, CHANNEL_ID, DEL_AFTER_TIME, DEL_AFTER_COUNT) VALUES (?, ?, ?, ?)", (server_id, channel_id, seconds, None))
                    await con.commit()
                
                embed = discord.Embed(title='Autodelete preparing channel', description=f'Autodelete has been started in {ctx.channel.mention} and will delete all previous messages.', color=0xFF7518, timestamp=datetime.now(timezone.utc))
                embed.set_footer(text=botversion)
                msg = await ctx.send(embed=embed)
                await msg.add_reaction("🔄")
                
                #This can take a while
                try:
                    await self.delete_before_command_start(ctx, time=seconds, count=None)
                except Exception as e:
                    print(f'Error in delete_before_command_start, time: \n\n {e} \n\n')
                
                get_channel = self.bot.get_channel(channel_id)
                done_embed = discord.Embed(title='Autodelete started', description=f'Autodelete has been started in {get_channel.mention} and will delete messages after {numeric_part} {unit_name}.', color=0x00ff00, timestamp=datetime.now(timezone.utc))
                done_embed.set_footer(text=botversion)
                msg1 = await get_channel.send(embed=done_embed)
                await msg1.add_reaction("✅")
            
            except aiosqlite.Error as e:
                embed = discord.Embed(title='Autodelete already running', description=f'Autodelete is already running in {ctx.channel.mention}.\n\nTo change autodelete settings the current autodelete needs to be stopped and a new one needs to be started', color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.set_footer(text=botversion)
                await ctx.send(embed=embed)
                print(f'Error in autodelete startup time: \n\n {e} \n\n')
        
        elif index_time == 1 and index_count == 1:
            try:
                #remove by message count and time in channel which ever comes first
                async with aiosqlite.connect(autodelete_database) as con:
                    async with con.execute("SELECT server_id FROM servers WHERE server_id = ?", (server_id,)) as cursor:
                        existing_server = await cursor.fetchone()
                    if existing_server:
                        await con.execute("INSERT INTO channels (SERVER_ID, CHANNEL_ID, DEL_AFTER_TIME, DEL_AFTER_COUNT) VALUES (?, ?, ?, ?)", (server_id, channel_id, seconds, count))
                    else:
                        await con.execute("INSERT INTO servers (SERVER_ID) VALUES (?)", (server_id,))
                        await con.execute("INSERT INTO channels (SERVER_ID, CHANNEL_ID, DEL_AFTER_TIME, DEL_AFTER_COUNT) VALUES (?, ?, ?, ?)", (server_id, channel_id, seconds, count))
                    await con.commit()
                
                embed = discord.Embed(title='Autodelete preparing channel', description=f'Autodelete has been started in {ctx.channel.mention} and will delete all previous messages.', color=0xFF7518, timestamp=datetime.now(timezone.utc))
                embed.set_footer(text=botversion)
                msg = await ctx.send(embed=embed)
                await msg.add_reaction("🔄")
                
                #This can take a while
                try:
                    await self.delete_before_command_start(ctx, time=seconds, count=count)
                except Exception as e:
                    print(f'Error in delete_before_command_start, time and count: \n\n {e} \n\n')
                
                get_channel = self.bot.get_channel(channel_id)
                done_embed = discord.Embed(title='Autodelete started', description=f'Autodelete has been started in {get_channel.mention} and will delete messages after {count} messages or {numeric_part} {unit_name} which ever comes first.', color=0x00ff00, timestamp=datetime.now(timezone.utc))
                done_embed.set_footer(text=botversion)
                msg1 = await get_channel.send(embed=done_embed)
                await msg1.add_reaction("✅")
            
            except aiosqlite.Error as e:
                embed = discord.Embed(title='Autodelete already running', description=f'Autodelete is already running in {ctx.channel.mention}.\n\nTo change autodelete settings the current autodelete needs to be stopped and a new one needs to be started', color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.set_footer(text=botversion)
                await ctx.send(embed=embed)
                print(f'Error in autodelete startup time and count: \n\n {e} \n\n')
        
        else:
            #arguments do not match any of the above so its not valid
            if index_count > 1 or index_time > 1:
                ctx._wrong_start_format_ = True
                ctx._error_reason_ = 'You can only have one of each argument a maximum of 2 arguments'
                raise commands.UserInputError
            elif index_count == 0 and index_time == 0:
                ctx._wrong_start_format_ = True
                ctx._error_reason_ = 'You must pass at least one argument'
                raise commands.UserInputError
            else:
                ctx._wrong_start_format_ = True
                ctx._error_reason_ = 'Something went wrong'
                raise commands.UserInputError
    
    @autodelete_base.command(name='list')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def autodelete_list(self, ctx):
        '''
        List all channels with autodelete activated in this server.
        '''
        async with aiosqlite.connect(autodelete_database) as con:
            async with con.execute("SELECT CHANNEL_ID, DEL_AFTER_TIME, DEL_AFTER_COUNT FROM channels WHERE SERVER_ID = ?", (ctx.guild.id,)) as cursor:
                channel_data = await cursor.fetchall()
            
            embed = discord.Embed(title=f"Autodelete Channels in {ctx.guild.name}", color=0x0000ff, timestamp=datetime.now(timezone.utc))
            if channel_data:
                for channel_id, del_after_time, del_after_count in channel_data:
                    channel = discord.utils.get(ctx.guild.channels, id=channel_id)
                    if del_after_time and del_after_count:
                        embed.add_field(name=f"Channel: {channel.mention if channel else 'No channel found but how?'}", value=f"Autodelete Time: {del_after_time} seconds\nAutodelete Count: {del_after_count} messages", inline=False)
                    elif del_after_time:
                        embed.add_field(name=f"Channel: {channel.mention if channel else 'No channel found but how?'}", value=f"Autodelete Time: {del_after_time} seconds", inline=False)
                    elif del_after_count:
                        embed.add_field(name=f"Channel: {channel.mention if channel else 'No channel found but how?'}", value=f"Autodelete Count: {del_after_count} messages", inline=False)                        
            else:
                embed.add_field(name=f"No channels with autodelete activated in this server.", value=f"Use {command_prefix}help autodelete to get more info on how to start autodelete", inline=False)
            embed.set_footer(text=botversion)
            await ctx.send(embed=embed)
    
    @autodelete_base.command(name='stop')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def autodelete_stop(self, ctx, channel:discord.TextChannel=None):
        '''
        Stop autodelete feature for the current channel.
        '''
        if channel is None:
            channel_id = ctx.channel.id
        else:
            channel_id = channel.id        
        
        #wait for on_message to add the stop command to the database otherwise it will remain in the database
        await asyncio.sleep(1)
        
        async with aiosqlite.connect(autodelete_database) as con:
                async with con.execute("SELECT channel_id FROM channels WHERE channel_id = ?", (channel_id,)) as cursor:
                    channel_in_database = await cursor.fetchone()
                
                channel_object = discord.utils.get(ctx.guild.channels, id=channel_id)
                if channel_in_database:
                    await con.execute("PRAGMA foreign_keys = ON")
                    await con.execute("DELETE FROM messages WHERE CHANNEL_ID = ?", (channel_id,))
                    await con.execute("DELETE FROM channels WHERE CHANNEL_ID = ?", (channel_id,))
                    await con.commit()
                    await ctx.reply(f"Autodelete feature has been stopped for {channel_object.mention}.", mention_author=False)
                else:
                    await ctx.reply(f"Autodelete feature is not active in {channel_object.mention}.", mention_author=False)
    
    @autodelete_start.error
    async def autodelete_start_error(self, ctx, error):
        '''
        Error handler for autodelete_start_error command.
        '''
        if isinstance(error, commands.UserInputError):
            if ctx._wrong_start_format_:
                reason = ctx._error_reason_
                embed = discord.Embed(title=f'{reason}', description=f'Please use the following format for start:\n`{command_prefix}autodelete start <[count] [time]>`\n\n\
                                    If `[count]` is set, messages are deleted after this amount of messages.\n\
                                    If `[time]` is set, messages are deleted after this amount of time.\n\
                                    If both `[count]` and `[time]` are set, messages are deleted after which ever comes first.\n\
                                    At least one of `[count]` or `[time]` must be set.\n\n\
                                    Examples:\n`{command_prefix}autodelete start 1000 3h`\n`{command_prefix}autodelete start 1000`\n`{command_prefix}autodelete start 3h`\n\n\
                                    Valid time formats are:\n`s, sec, secs, second, seconds`\n`m, min, mins, minute, minutes`\n`h, hr, hrs, hour, hours`\n`d, day, days`\n`w, week, weeks`\n`month, months`', color=0xFFFF00, timestamp=datetime.now(timezone.utc))
                embed.set_footer(text=botversion)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY*3)
                ctx._ignore_ = True
    
    async def cog_unload(self):
        # print('Autodelete cog_unload stopping monitor_expired_messages loop')
        if self.monitor_expired_messages_task and not self.monitor_expired_messages_task.done():
            self.monitor_expired_messages_task.cancel()
    
    async def cog_load(self):
        await asyncio.sleep(2)
        # print('Autodelete cog_load starting monitor_expired_messages loop')
        if self.monitor_expired_messages_task and self.monitor_expired_messages_task.done():
            loop = asyncio.get_event_loop()
            self.monitor_expired_messages_task = loop.create_task(self.monitor_expired_messages_loop())
            await self.fetch_missed_messages()
    
    @commands.Cog.listener()
    async def on_disconnect(self):
        if self.monitor_expired_messages_task and not self.monitor_expired_messages_task.done():
            self.monitor_expired_messages_task.cancel()
    
    @commands.Cog.listener()
    async def on_resumed(self):
        await asyncio.sleep(2)
        if self.monitor_expired_messages_task and self.monitor_expired_messages_task.done():
            loop = asyncio.get_event_loop()
            self.monitor_expired_messages_task = loop.create_task(self.monitor_expired_messages_loop())
            await self.fetch_missed_messages()
    
    async def monitor_expired_messages_loop(self):
        while True:
            # print ('monitor_expired_messages_loop')
            await asyncio.sleep(SECOND_LOOP_DELAY)
            self.loopcounter += SECOND_LOOP_DELAY
            await self.get_expired_messages()
            # print('inside loop')
            
            #run every 60 seconds as a cleanup and background check
            if self.loopcounter % 60 == 0:
                self.loopcounter = 0
                await self.fetch_missed_messages()
                # print('monitor_expired_messages_loop 60sec cleanup')

async def setup(bot):
    await bot.add_cog(Autodelete(bot))
