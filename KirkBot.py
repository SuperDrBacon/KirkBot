#!/usr/bin/env python3

import asyncio
import os
import traceback

import discord
from discord.ext import commands

import cogs.utils.functions as functions
from cogs.utils.constants import (ARCHIVE_DATABASE, AUTODELETE_DATABASE,
                                  AUTOROLE_DATABASE, BOTVERSION, CARDSPATH,
                                  COMMAND_LOGS_DATABASE, COMMAND_PREFIX,
                                  DICEPATH, ECONOMY_DATABASE, EMOJIPATH,
                                  FLAGPATH, IMAGEMOD_DATABASE, IMAGEPATH,
                                  INVITELOG_DATABASE, OSPATH,
                                  PERMISSIONS_DATABASE, TOKEN)
from cogs.utils.helpcommand import ButtonHelpCommand


def main_program():
    print('Logging in...')
    
    intents = discord.Intents().all()
    bot = commands.Bot(command_prefix=COMMAND_PREFIX, help_command=ButtonHelpCommand(), case_insensitive=True, intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'{BOTVERSION} main online')
    
    @bot.event
    async def on_connect():
        print(f'{BOTVERSION} connected successfully.')
    
    @bot.event
    async def on_disconnect():
        print(f'{BOTVERSION} disconnected.')
    
    @bot.event
    async def on_resumed():
        print(f'{BOTVERSION} resumed.')
    
    # @bot.event
    # async def on_error(event, *args, **kwargs):
    #     print(f'{title}, {event} error: {args}, {kwargs}')
    #     with open(rf'{OSPATH}/error.txt', 'a') as f:
    #         f.write(f'ERROR EVENT-> {event}. ARGS -> {args}. KWARGS -> {kwargs}\n')
    
    async def loadCogs():
        for filename in os.listdir(rf'{OSPATH}/cogs'):
            if filename.endswith('.py'):
                name = filename[:-3]
                try:
                    await bot.load_extension(f'cogs.{name}')
                except Exception as e:
                    print(f'Error when loading module because: {e} and traceback: {traceback.format_exc()}')
    
    async def check_files():
        functions.checkForDir(EMOJIPATH)
        functions.checkForDir(CARDSPATH)
        functions.checkForDir(DICEPATH)
        functions.checkForDir(IMAGEPATH)
        await functions.checkForFile(filepath=OSPATH, filename='info.ini', database=False) 
        await functions.checkForFile(filepath=OSPATH, filename='config.ini', database=False) 
        await functions.checkForFile(filepath=os.path.dirname(FLAGPATH),             filename=os.path.basename(FLAGPATH),                database=False)
        await functions.checkForFile(filepath=os.path.dirname(ARCHIVE_DATABASE),     filename=os.path.basename(ARCHIVE_DATABASE),        database=True, dbtype='archive')
        await functions.checkForFile(filepath=os.path.dirname(AUTODELETE_DATABASE),  filename=os.path.basename(AUTODELETE_DATABASE),     database=True, dbtype='autodelete')
        await functions.checkForFile(filepath=os.path.dirname(AUTOROLE_DATABASE),    filename=os.path.basename(AUTOROLE_DATABASE),       database=True, dbtype='autorole')
        await functions.checkForFile(filepath=os.path.dirname(COMMAND_LOGS_DATABASE),filename=os.path.basename(COMMAND_LOGS_DATABASE),   database=True, dbtype='command_logs')
        await functions.checkForFile(filepath=os.path.dirname(ECONOMY_DATABASE),     filename=os.path.basename(ECONOMY_DATABASE),        database=True, dbtype='economy')
        await functions.checkForFile(filepath=os.path.dirname(IMAGEMOD_DATABASE),     filename=os.path.basename(IMAGEMOD_DATABASE),      database=True, dbtype='imagemod')
        await functions.checkForFile(filepath=os.path.dirname(INVITELOG_DATABASE),   filename=os.path.basename(INVITELOG_DATABASE),      database=True, dbtype='invitelog')
        await functions.checkForFile(filepath=os.path.dirname(PERMISSIONS_DATABASE), filename=os.path.basename(PERMISSIONS_DATABASE),    database=True, dbtype='permissions')
    
    async def main_start():
        await check_files()
        await loadCogs()
        await bot.start(TOKEN)
    
    try:
        asyncio.run(main_start())
    except Exception as e:
        print(f'Error when logging in: {e} and traceback: {traceback.format_exc()}')

if __name__ == '__main__':
    main_program()