#!/usr/bin/env python3

import asyncio
import traceback
import discord
import os
import cogs.utils.functions as functions
from discord.ext import commands
from configparser import ConfigParser
from cogs.utils.helpcommand import NewHelpCommand

path = os.path.abspath(os.getcwd())

def mainProgram():
    print('Logging in...')
    info = ConfigParser()
    config = ConfigParser()
    functions.checkForFile(path, 'info.ini') 
    functions.checkForFile(path, 'config.ini') 
    info.read(rf'{path}/info.ini')
    config.read(rf'{path}/config.ini')
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
    #     with open(rf'{path}/error.txt', 'a') as f:
    #         f.write(f'ERROR EVENT-> {event}. ARGS -> {args}. KWARGS -> {kwargs}\n')
    
    async def loadCogs():
        for filename in os.listdir(rf'{path}/cogs'):
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