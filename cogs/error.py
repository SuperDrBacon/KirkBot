import traceback
import discord

from discord.ext import commands
from datetime import datetime, timezone
from cogs.utils.constants import BOTVERSION, COMMAND_PREFIX, MSG_DEL_DELAY

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
                embed = discord.Embed(title=f"Error description", description=f"I couldn't send this information to you via direct message. Are your DMs enabled?", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error techincal", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.MissingRequiredArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"You missed the argument `{error.param.name}` for this command!", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error techincal", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.MissingPermissions):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Missing permissions: {error.missing_permissions}", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error techincal", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
            
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
                embed = discord.Embed(title=f"Error description", description=f"I can't understand this command message! Please check `{COMMAND_PREFIX}help {ctx.command}`", color=0xff0000, timestamp=datetime.now(timezone.utc))
                if str(error).startswith('Converting to \"float\" failed for parameter'):
                    embed.add_field(name="Error techincal", value=f"Please use a dot '.' as a decimal separator when passing a nummer in a command", inline=False)
                else:
                    embed.add_field(name="Error techincal", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.CommandNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"No such command found. Try `{COMMAND_PREFIX}help`", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error techincal", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
            
        elif isinstance(error, commands.CommandOnCooldown):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"This command is on cooldown bozo. Try again in {error.retry_after:.2f} seconds.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.CommandError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(name="Error description", description=f"The command you've entered could not be completed at this time.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                print(f'CONSOLE ONLY, COMMAND FAILED: {error}')        
        else:            
            print(f'CONSOLE ONLY, ALL FAILED: {error} and {traceback.format_exc()}')

async def setup(bot):
    await bot.add_cog(Error(bot))
