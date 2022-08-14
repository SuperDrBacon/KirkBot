from configparser import ConfigParser
import os
import discord
import datetime
from discord import Embed
from discord.ext import commands

path = os.path.abspath(os.getcwd())
info = ConfigParser()
info.read(rf'{path}/info.ini')

botversion = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']
timestamp = datetime.datetime.now()

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.group(name='help', invoke_without_command=True)
    async def help_base(self, ctx):
        embed = Embed(title='Help commands per group', color=discord.Colour.gold(), timestamp=timestamp)
        embed.add_field(name="Fun", value="`.,ping`\n`.,8ball`\n`.,checkem` `.,check` `.,c`\n`.,bigletter` `.,em`\n`.,braille` `.,br`\n`.,youtube` `.,yt`\n`.,tag` `.,tag get`\n`.,gcp` `.,gcp full`", inline=True)
        embed.add_field(name="AI", value="`.,ai`", inline=True) #\n`@David Marcus`
        embed.add_field(name="Admin", value="`.,botstatus`\n`.,botstatus set`\n`.,flag @user emoji`\n`.,flag remove @user`", inline=True)
        embed.add_field(name="Moderator", value="`No commands lmao`", inline=True)
        embed.add_field(name='―――――――――――――――――――', value='Use .,help [group] to see command aliases and descriptions', inline=False)
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed)
        
    @help_base.command(name='fun', invoke_without_command=True)
    async def help_fun(self, ctx,):
        embed = Embed(title='Help -> Fun', color=discord.Colour.green(), timestamp=timestamp)
        embed.add_field(name="Commands and descriptions", 
                        value="`.,8ball` Ask the 8ball your burning questions\n"+
                            "`.,checkem, .,check, .,c` Generate random number and maybe check those dubs\n"+
                            "`.,bigletter, .,em` Convert your message into emoji letters\n"+
                            "`.,braille, .,br` Convert your message into braille so blind people can read it\n"+
                            "`.,youtube, .,yt` Input a search and get the first Youtube result back\n"+
                            "`.,tag, .,tag get` Tag another person in the server when you're tagged! Or see who is currently tagged\n"+
                            "`.,gcp, .,gcp full` Get the current position of the Global Consciousness Project Dot. Use full to get an explanation of the different colours")
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed,)
        
    @help_base.command(name='ai', invoke_without_command=True)
    async def help_AI(self, ctx,):
        embed = Embed(title='Help -> AI', color=discord.Colour.blue(), timestamp=timestamp)
        embed.add_field(name="Commands and descriptions", 
                        value="`.,ai` Talk to the GPT-3 bot and get a response\n"+
                            "`@David Marcus` Uses the custom AI model created from chat messages\n"+
                            "`Reply to the bot` Replying to the bot will take previous messages into account when generating a response")
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed,)
        
    @help_base.command(name='admin', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def help_admin(self, ctx):
        embed = Embed(title='Help -> Admin', color=discord.Colour.red(), timestamp=timestamp)
        embed.add_field(name="Commands and descriptions", 
                        value="`.,botstatus` See what the current bot status is\n"+
                            "`.,botstatus set [message]` Set the bot status to something else\n"+
                            "`.,flag @user [emoji]` Flag a user in the server and the bot will keep reacting the emoji\n"+
                            "`.,flag remove @user` Remove the flag from the user")
        embed.set_footer(text=botversion)
        await ctx.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Help(bot))
