import os
import discord
import tweepy
from discord.ext import commands
from configparser import ConfigParser


config = ConfigParser(interpolation=None)
configpath = os.path.abspath(os.getcwd())
configini = '\\'.join([configpath, "config.ini"])
config.read(configini)

APIkey = config['TWITTER']['APIkey']
APIkeysecret = config['TWITTER']['APIkeysecret']
# BearerToken = config['TWITTER']['BearerToken']
AccessToken = config['TWITTER']['AccessToken']
AccessTokenSecret = config['TWITTER']['AccessTokenSecret']
# clientID = config['TWITTER']['clientID']
# clientsecret = config['TWITTER']['clientsecret']

auth = tweepy.OAuthHandler(APIkey, APIkeysecret)
auth.set_access_token(AccessToken, AccessTokenSecret)
api = tweepy.API(auth)

class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('twitter module online')
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        pass
    
    @commands.has_permissions(administrator=True)
    @commands.group(aliases=["tweet"], invoke_without_command=True)
    async def twittercommand(self, ctx):
        
        pass

def setup(bot):
    bot.add_cog(Twitter(bot))


# url = f"https://twitter.com/user/status/{tweet.id}"