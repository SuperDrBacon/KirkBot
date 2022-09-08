import discord
import asyncio
import os
import traceback
from discord.ext import commands

MSG_DEL_DELAY = 5

class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Errorlogging module online')
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, "original", error)

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("I couldn't send this information to you via direct message. Are your DMs enabled?")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"You missed the argument `{error.param.name}` for this command!")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(f"Missing permissions: {error.missing_permissions}")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, discord.Forbidden):
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await msg.reply(f"This person is a bot blocker.")
            # await ctx.message.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.UserInputError):
            await ctx.send(f"I can't understand this command message! Please check `.,help {ctx.command}`")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(f"No such command found. Try `.,help`")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown retard. Try again in {error.retry_after:.2f} seconds.")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.CommandError):
            await ctx.send("The command you've entered could not be completed at this time.")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            print(f'CONSOLE ONLY, COMMAND FAILED: {error}')        
        else:            
            print(f'CONSOLE ONLY, ALL FAILED: {error}')

async def setup(bot):
    await bot.add_cog(Error(bot))
