from ast import alias
from configparser import ConfigParser
import os
import discord
import datetime
from discord import Embed
from discord.ext import commands

path = os.path.abspath(os.getcwd())
info = ConfigParser()
config = ConfigParser()
info.read(rf'{path}/info.ini')
config.read(rf'{path}/config.ini')

command_prefix = config['BOTCONFIG']['prefix']
botversion = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']
timestamp = datetime.datetime.now()

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.group(name='help', invoke_without_command=True)
    async def help_base(self, ctx):
        embed = Embed(title='Help commands per group', color=discord.Colour.gold(), timestamp=timestamp)
        embed.add_field(name="Fun", value=f"`{command_prefix}ping`\n`{command_prefix}8ball`\n`{command_prefix}checkem` `{command_prefix}check` `{command_prefix}c`\n`{command_prefix}bigletter` `{command_prefix}em`\n`{command_prefix}braille` `{command_prefix}br`\n`{command_prefix}youtube` `{command_prefix}yt`\n`{command_prefix}tag` `{command_prefix}tag get`\n`{command_prefix}gcp` `{command_prefix}gcp full`\n`{command_prefix}wordcloud` `{command_prefix}wc`", inline=True)
        embed.add_field(name="AI", value=f"`{command_prefix}ai`", inline=True) #\n`@David Marcus`
        embed.add_field(name="Admin", value=f"`{command_prefix}botstatus`\n`{command_prefix}botstatus set`\n`{command_prefix}flag @user emoji`\n`{command_prefix}flag remove @user`\n`{command_prefix}flag toggle`", inline=True)
        embed.add_field(name="Moderator", value=f"`No commands lmao`", inline=True)
        embed.add_field(name='―――――――――――――――――――', value=f'Use {command_prefix}help [group] to see command aliases and descriptions', inline=False)
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed)
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @help_base.group(name='fun', invoke_without_command=True)
    async def help_fun(self, ctx):
        embed = Embed(title='Help -> Fun', color=discord.Colour.green(), timestamp=timestamp)
        embed.add_field(name="Commands and descriptions", 
                        value=f"`{command_prefix}8ball` Ask the 8ball your burning questions\n"+
                            f"`{command_prefix}checkem, {command_prefix}check, {command_prefix}c` Generate random number and maybe check those dubs\n"+
                            f"`{command_prefix}bigletter, {command_prefix}em` Convert your message into emoji letters\n"+
                            f"`{command_prefix}braille, {command_prefix}br` Convert your message into braille so blind people can read it\n"+
                            f"`{command_prefix}youtube, {command_prefix}yt` Input a search and get the first Youtube result back\n"+
                            f"`{command_prefix}tag, {command_prefix}tag get` Tag another person in the server when you're tagged! Or see who is currently tagged\n"+
                            f"`{command_prefix}gcp, {command_prefix}gcp full` Get the current position of the Global Consciousness Project Dot. Use full to get an explanation of the different colours\n"+
                            f"`{command_prefix}wordcloud, {command_prefix}wc` Get a wordcloud of the channel or server. Specify 'server' or 'channel' as the first argument and the amount of messages as the second argument. E.g `{command_prefix}wc server 1000`. Default amount is 100000 to get basically all messages")
        embed.add_field(name='―――――――――――――――――――', value=f'Use {command_prefix}help fun [command] to see further command descriptions', inline=False)
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed)
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @help_fun.command(name='wordcloud', aliases=['wc'], invoke_without_command=True)
    async def help_wordcloud(self, ctx):
        embed = Embed(title='Help -> Fun -> Wordcloud', color=discord.Colour.green(), timestamp=timestamp)
        embed.add_field(name="Wordcloud description", 
                        value=f"\n`{command_prefix}wordcloud, {command_prefix}wc`\nGet a wordcloud of the channel or server. Specify 'server' or 'channel' as the first argument and the amount of messages as the second argument. E.g `{command_prefix}wc server 1000`. Default amount is 100000 to get basically all messages")
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed)
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @help_base.command(name='ai', invoke_without_command=True)
    async def help_AI(self, ctx):
        embed = Embed(title='Help -> AI', color=discord.Colour.blue(), timestamp=timestamp)
        embed.add_field(name="Commands and descriptions", 
                        value=f"`{command_prefix}ai` Talk to the GPT-3 bot and get a response\n"+
                            f"`@David Marcus` Uses the custom AI model created from chat messages\n"+
                            f"`Reply to the bot` Replying to the bot will take previous messages into account when generating a response")
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed)
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    # @commands.has_permissions(administrator=True)
    @help_base.command(name='admin', invoke_without_command=True)
    async def help_admin(self, ctx):
        embed = Embed(title='Help -> Admin', color=discord.Colour.red(), timestamp=timestamp)
        embed.add_field(name="Commands and descriptions", 
                        value=f"`{command_prefix}botstatus` See what the current bot status is\n"+
                            f"`{command_prefix}botstatus set [message]` Set the bot status to something else\n"+
                            f"`{command_prefix}flag @user [emoji]` Flag a user in the server and the bot will keep reacting the emoji\n"+
                            f"`{command_prefix}flag remove @user` Remove the flag from the user\n"+
                            f"`{command_prefix}flag toggle` Toggle the channel to be include to post flags on users. Channel not included by default")
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
