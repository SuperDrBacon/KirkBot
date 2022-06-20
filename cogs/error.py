import discord
import asyncio
import os
import traceback
from discord.ext import commands

class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Errorlogging module online')
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, "original", error)

        if isinstance(error, (discord.Forbidden, commands.NoPrivateMessage)):
            await ctx.send("I couldn't send this information to you via direct message. Are your DMs enabled?")
            
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"You missed the argument `{error.param.name}` for this command!")
            
        elif isinstance(error, commands.UserInputError):
            await ctx.send(f"I can't understand this command message! Please check `.,help {ctx.command}`")
            
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(f"No such command found. Try `.,help`")
            
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown retard. Try again in {error.retry_after:.2f} seconds.")
            
        else:
            await ctx.send("The command you've entered could not be completed at this time.")
            print(error)

def setup(bot):
    bot.add_cog(Error(bot))
