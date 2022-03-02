from configparser import ConfigParser
import os
import discord
import datetime
from discord.ext import commands

config = ConfigParser()
configpath = os.path.abspath(os.getcwd())
configini = '\\'.join([configpath, "config.ini"])
config.read(configini)

botversion = config['DEFAULT']['title']
timestamp = datetime.datetime.now()

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.group(name='help', invoke_without_command=True)
    async def help_base(self, ctx):
        embed = discord.Embed(title='Help commands per group', color=discord.Colour.gold(), timestamp=timestamp)
        embed.add_field(name="Fun", value="`.,ping`\n`.,8ball`\n`.,checkem` `.,check` `.,c`\n`.,bigletter` `.,em`\n`.,braille` `.,br`\n`.,youtube` `.,yt`\n", inline=True)
        embed.add_field(name="AI", value="`.,ai`\n`@David Marcus`", inline=True)
        embed.add_field(name="Admin", value="`.,botstatus`\n`.,botststus set`", inline=True)
        embed.add_field(name="Moderator", value="`No commands lmao`", inline=True)
        embed.add_field(name='―――――――――――――――――――', value='Use .,help [group] to see command aliases and descriptions', inline=False)
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed)
        
    @help_base.command(name='fun', invoke_without_command=True)
    async def help_fun(self, ctx,):
        embed = discord.Embed(title='Help -> Fun', color=discord.Colour.green(), timestamp=timestamp)
        embed.add_field(name="Commands and descriptions", value="`.,8ball` Ask the 8ball your burning questions\n`.,checkem, .,check, .,c` Generate random number and maybe check those dubs\n`.,bigletter, .,em` Convert your message into emoji letters\n`.,braille, .,br` Convert your message into braille so blind people can read it\n`.,youtube, .,yt` Input a search and get the first Youtube result back")
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed,)
        
    @help_base.command(name='ai', invoke_without_command=True)
    async def help_AI(self, ctx,):
        embed = discord.Embed(title='Help -> AI', color=discord.Colour.blue(), timestamp=timestamp)
        embed.add_field(name="Commands and descriptions", value="`.,ai` Talk to the GPT-3 bot and get a response\n`@David Marcus` Uses the custom AI model created from chat messages\n`Reply to the bot` Replying to the bot will take previous messages into account when generating a response")
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed,)
        
    @help_base.command(name='admin', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def help_admin(self, ctx):
        embed = discord.Embed(title='Help -> Admin', color=discord.Colour.red(), timestamp=timestamp)
        embed.add_field(name="Commands and descriptions", value="`.,botstatus` See what the current bot status is\n`.,botstatus set [message]` Set the bot status to something else\n")
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Help(bot))
