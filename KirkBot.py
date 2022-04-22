import discord
import os
from discord.ext import commands
from configparser import ConfigParser

print("Logging in...")
config = ConfigParser()
configpath = os.path.dirname(os.path.realpath(__file__))
configini = '/'.join([configpath, "config.ini"])
config.read(configini)
path = os.path.abspath(os.getcwd())
print(os.name)
title = config['DEFAULT']['title']
intents = discord.Intents().all()

bot = commands.Bot(command_prefix=config['BOTCONFIG']['prefix'], help_command=None, case_insensitive=True, intents=intents)

for filename in os.listdir(path + "/cogs"):
    if filename.endswith('.py'):
        name = filename[:-3]
        try:
            bot.load_extension(f"cogs.{name}")
        except Exception as e:
            print(f"Error when loading module because: {e}")

try:
    bot.run(config['BOTCONFIG']['token'])
except Exception as e:
    print(f"Error when logging in: {e}")


@bot.event
async def on_ready():
    print(f'{title} main online')

@bot.event
async def on_connect():
    print(f'{title} connected successfully.')

@bot.event
async def on_disconnect():
    print(f'{title} disconnected.')