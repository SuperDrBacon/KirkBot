#!/usr/bin/env python3

import asyncio
import traceback
import discord
import os
import cogs.utils.functions as functions
from discord.ext import commands
from configparser import ConfigParser
from cogs.utils.helpcommand import NewHelpCommand

ospath = os.path.abspath(os.getcwd())
archive_database = rf'{ospath}/cogs/archive_data.db'
autodelete_database = rf'{ospath}/cogs/autodelete_data.db'
autorole_database = rf'{ospath}/cogs/autorole_data.db'
command_logs_data = rf'{ospath}/cogs/command_logs.db'
economy_data = rf'{ospath}/cogs/economy_data.db'
invitelog_database = rf'{ospath}/cogs/invitelog_data.db'
permissions_data = rf'{ospath}/cogs/permissions_data.db'

def mainProgram():
    print('Logging in...')
    
    functions.checkForFile(filepath=ospath, filename='info.ini', database=False) 
    functions.checkForFile(filepath=ospath, filename='config.ini', database=False) 
    functions.checkForFile(filepath=os.path.dirname(archive_database),    filename=os.path.basename(archive_database),    database=True, dbtype='archive')
    functions.checkForFile(filepath=os.path.dirname(autodelete_database), filename=os.path.basename(autodelete_database), database=True, dbtype='autodelete')
    functions.checkForFile(filepath=os.path.dirname(autorole_database),   filename=os.path.basename(autorole_database),   database=True, dbtype='autorole')
    functions.checkForFile(filepath=os.path.dirname(command_logs_data),   filename=os.path.basename(command_logs_data),   database=True, dbtype='command_logs')
    functions.checkForFile(filepath=os.path.dirname(economy_data),        filename=os.path.basename(economy_data),        database=True, dbtype='economy')
    functions.checkForFile(filepath=os.path.dirname(invitelog_database),  filename=os.path.basename(invitelog_database),  database=True, dbtype='invitelog')
    functions.checkForFile(filepath=os.path.dirname(permissions_data),    filename=os.path.basename(permissions_data),    database=True, dbtype='permissions')
    
    info, config = ConfigParser(), ConfigParser()
    info.read(rf'{ospath}/info.ini')
    config.read(rf'{ospath}/config.ini')
    title = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']
    intents = discord.Intents().all()
    
    bot = commands.Bot(command_prefix=config['BOTCONFIG']['prefix'], help_command=NewHelpCommand(), case_insensitive=True, intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'{title} main online')
    
    @bot.event
    async def on_connect():
        print(f'{title} connected successfully.')
    
    @bot.event
    async def on_disconnect():
        print(f'{title} disconnected.')
    
    @bot.event
    async def on_resumed():
        print(f'{title} resumed.')
    
    # @bot.event
    # async def on_error(event, *args, **kwargs):
    #     print(f'{title}, {event} error: {args}, {kwargs}')
    #     with open(rf'{ospath}/error.txt', 'a') as f:
    #         f.write(f'ERROR EVENT-> {event}. ARGS -> {args}. KWARGS -> {kwargs}\n')
    
    async def loadCogs():
        for filename in os.listdir(rf'{ospath}/cogs'):
            if filename.endswith('.py'):
                name = filename[:-3]
                try:
                    await bot.load_extension(f'cogs.{name}')
                except Exception as e:
                    print(f'Error when loading module because: {e} and traceback: {traceback.format_exc()}')
    
    async def mainStart():
        await loadCogs()
        await bot.start(config['BOTCONFIG']['token'])
    
    try:
        asyncio.run(mainStart())
    except Exception as e:
        print(f'Error when logging in: {e} and traceback: {traceback.format_exc()}')

if __name__ == '__main__':
    mainProgram()