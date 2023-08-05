import os
import discord
from configparser import ConfigParser
from discord.ext import commands

ospath = os.path.abspath(os.getcwd())
config = ConfigParser()
config.read(rf'{ospath}/config.ini')
owner_id = int(config['BOTCONFIG']['ownerid'])

MSG_DEL_DELAY = 5

class AdminCommands(commands.Cog):
    '''
    This module contains commands used by admins.
    '''
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
            print('Admin module online')
    
    
    
    @commands.has_permissions(administrator=True)
    @commands.command(name='webhook', aliases=["wh"], hidden=True)
    async def webhook(self, ctx, webhook_name:str, message:str):
        '''
        Create a new webhook in the current channel with the given name and send a message using it. 
        The message can contain any text and will be sent as the webhook's username. 
        This command is hidden and can only be used by authorized users.
        '''
        # async def create_webhook():
        #     server_id = ctx.guild.id
        #     channel_id = ctx.channel.id
        #     webhook_avatar_url = self.bot.user.avatar.url
        #     server = self.bot.get_guild(server_id)
        #     channel = server.get_channel(channel_id)
        #     webhook = await channel.create_webhook(name=webhook_name, avatar=webhook_avatar_url)
        #     return webhook
        
        # async def send_webhook_message(content:str):
        #     webhook = await create_webhook()
        #     await webhook.send(content)
        
        # async def my_function(mesage:str):
        #     await send_webhook_message(mesage)
        
        # await my_function(message)
        server_id = ctx.guild.id
        channel_id = ctx.channel.id
        server = self.bot.get_guild(server_id)
        channel = server.get_channel(channel_id)
        # webhook_avatar_url:str = self.bot.user.avatar.url
        webhook_avatar_url = 'https://cdn.discordapp.com/avatars/988870398278004757/712d9a6bb8a33ffe767182c9886a6385.png'
        print (webhook_avatar_url)
        webhook = await channel.create_webhook(name=str(webhook_name), avatar='https://cdn.discordapp.com/avatars/988870398278004757/712d9a6bb8a33ffe767182c9886a6385.png')
        await webhook.send(message)
        print (webhook.url)
    
async def setup(bot):
    await bot.add_cog(AdminCommands(bot))