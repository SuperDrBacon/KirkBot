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
title = config['DEFAULT']['title']

bot = commands.Bot(command_prefix=config['BOTCONFIG']['prefix'])

@bot.event
async def on_ready():
    print(f'{title} main online')


for filename in os.listdir(path + "/cogs"):
    if filename.endswith('.py'):
        name = filename[:-3]
        bot.load_extension(f"cogs.{name}")

try:
    bot.run(config['BOTCONFIG']['token'])
except Exception as e:
    print(f"Error when logging in: {e}")

