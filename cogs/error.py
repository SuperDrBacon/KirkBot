import discord
import asyncio
import os
import traceback
from discord.ext import commands
from configparser import ConfigParser

path = os.path.abspath(os.getcwd())
config = ConfigParser()
config.read(rf'{path}/config.ini')
command_prefix = config['BOTCONFIG']['prefix']

MSG_DEL_DELAY = 8

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
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                bot_msg = await ctx.reply("I couldn't send this information to you via direct message. Are your DMs enabled?")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await bot_msg.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.MissingRequiredArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                bot_msg = await ctx.reply(f"You missed the argument `{error.param.name}` for this command!")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await bot_msg.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.MissingPermissions):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                bot_msg = await ctx.reply(f"Missing permissions: {error.missing_permissions}")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await bot_msg.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, discord.Forbidden):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                bot_msg = await msg.reply(f"This person is a bot blocker.")
                # await ctx.message.delete(delay=MSG_DEL_DELAY)
                # await bot_msg.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.UserInputError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                bot_msg = await ctx.reply(f"I can't understand this command message! Please check `{command_prefix}help {ctx.command}`")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await bot_msg.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.CommandNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                bot_msg = await ctx.reply(f"No such command found. Try `{command_prefix}help`")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await bot_msg.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.CommandOnCooldown):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                bot_msg = await ctx.reply(f"This command is on cooldown retard. Try again in {error.retry_after:.2f} seconds.")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await bot_msg.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.CommandError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                bot_msg = await ctx.reply("The command you've entered could not be completed at this time.")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await bot_msg.delete(delay=MSG_DEL_DELAY)
                print(f'CONSOLE ONLY, COMMAND FAILED: {error}')        
        else:            
            print(f'CONSOLE ONLY, ALL FAILED: {error} and {traceback.format_exc()}')

async def setup(bot):
    await bot.add_cog(Error(bot))
