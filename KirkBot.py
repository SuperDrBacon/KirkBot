#!/usr/bin/env python3

import discord
import os
from discord.ext import commands
from configparser import ConfigParser

def main():
    print('Logging in...')
    path = os.path.abspath(os.getcwd())
    info = ConfigParser()
    config = ConfigParser()
    info.read(rf'{path}/info.ini')
    config.read(rf'{path}/config.ini')
    title = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']
    intents = discord.Intents().all()

    bot = commands.Bot(command_prefix=config['BOTCONFIG']['prefix'], help_command=None, case_insensitive=True, intents=intents)

    for filename in os.listdir(rf'{path}/cogs'):
        if filename.endswith('.py'):
            name = filename[:-3]
            try:
                bot.load_extension(f'cogs.{name}')
            except Exception as e:
                print(f'Error when loading module because: {e}')

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

    @bot.event
    async def on_error(event, *args, **kwargs):
        print(f'{title}, {event} error: {args}, {kwargs}')
        with open(rf'{path}/error.txt', 'a') as f:
            f.write(f'ERROR EVENT-> {event}. ARGS -> {args}. KWARGS -> {kwargs}\n')

    try:
        bot.run(config['BOTCONFIG']['token'])
    except Exception as e:
        print(f'Error when logging in: {e}')

if __name__ == '__main__':
    main()
