from calendar import c
import os
import random
import discord
import tweepy
from discord.ext import commands, tasks
from configparser import ConfigParser


path = os.path.abspath(os.getcwd())
config = ConfigParser()
config.read(rf'{path}/config.ini')

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
    
    
    #@commands.has_permissions(administrator=True)
    @commands.group(aliases=['tweet'], invoke_without_command=True)
    async def tweet_base(self, ctx):
        await ctx.send('refer to help command for more info')
        #pass
    
    @tweet_base.command(name='currentstream', aliases=['cs'], invoke_without_command=True)
    async def tweet_currentstream(self, ctx):
        if self.get_tweet_stream.is_running():
            current = self.get_tweet_stream.get_task()
            await ctx.send(f'current stream is: {current}')
        else:
            await ctx.send('no stream is running')
        #pass
    
    @commands.has_permissions(administrator=True)
    @tweet_base.command(name='gettweets', aliases=['gt'], invoke_without_command=True)
    async def twitter_command(self, ctx, interval: int = 10, *, input: str = None):
        self.get_tweet_stream.start(input=input, ctx=ctx)
        self.get_tweet_stream.change_interval(minutes=interval)
        #pass
            
    @commands.has_permissions(administrator=True)
    @tweet_base.command(name='stopstream', aliases=['st'], invoke_without_command=True)
    async def stop_stream(self, ctx):
        self.get_tweet_stream.stop()
        await ctx.send('stream stopped')
        #pass
    
    @tasks.loop(reconnect=True)
    async def get_tweet_stream(self, input, ctx):
        await ctx.send(input)
        newinterval = random.randint(30, 120)
        self.get_tweet_stream.change_interval(minutes=newinterval)
        #pass
    
    @get_tweet_stream.before_loop
    async def before_get_tweet_stream(self):
        print('Waiting to start get_tweet_stream')
        await self.bot.wait_until_ready()
        print('get_tweet_stream started')
        
    def cog_unload(self):
        self.get_tweet_stream.cancel()

def setup(bot):
    bot.add_cog(Twitter(bot))


# url = f"https://twitter.com/user/status/{tweet.id}"