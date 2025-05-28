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
        
        # Argument and Parameter Errors
        elif isinstance(error, commands.MissingRequiredAttachment):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"This command requires an attachment!", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.BadArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Invalid argument provided. Please check your input.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.TooManyArguments):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Too many arguments provided for this command!", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.BadUnionArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Invalid argument type. Please check the expected format.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.BadLiteralArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Invalid choice. Please use one of the allowed values.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.BadColourArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Invalid color format. Please use hex format (#RRGGBB)", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.BadColorArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Invalid color format. Please use hex format (#RRGGBB)", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.BadBoolArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Invalid boolean value. Please use 'true', 'false'", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.BadInviteArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Invalid invite link provided.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.RangeError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Value is out of the allowed range.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        # Permission and Role Errors
        elif isinstance(error, commands.BotMissingPermissions):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"I'm missing permissions: {error.missing_permissions}", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.MissingRole):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"You're missing the required role: {error.missing_role}", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.BotMissingRole):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"I'm missing the required role: {error.missing_role}", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.MissingAnyRole):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"You're missing any of the required roles: {error.missing_roles}", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.BotMissingAnyRole):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"I'm missing any of the required roles: {error.missing_roles}", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.NotOwner):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"This command is restricted to the bot owner only.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        # Object Not Found Errors
        elif isinstance(error, commands.MessageNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified message could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.MemberNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified member could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.UserNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified user could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.GuildNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified guild/server could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.ChannelNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified channel could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.ThreadNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified thread could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.RoleNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified role could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.EmojiNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified emoji could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.GuildStickerNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified sticker could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.ScheduledEventNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified scheduled event could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.SoundboardSoundNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified soundboard sound could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.ObjectNotFound):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"The specified object could not be found.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        # Channel and Access Errors
        elif isinstance(error, commands.PrivateMessageOnly):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"This command can only be used in private messages.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.ChannelNotReadable):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"I cannot read messages in the specified channel.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.NSFWChannelRequired):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"This command can only be used in NSFW channels.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        # Check Errors
        elif isinstance(error, commands.CheckAnyFailure):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"You don't meet any of the required conditions to use this command.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.CheckFailure):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"You don't have permission to use this command.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        # Command State Errors
        elif isinstance(error, commands.DisabledCommand):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"This command is currently disabled.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.MaxConcurrencyReached):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Maximum concurrent uses of this command reached. Please try again later.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.CommandInvokeError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"An error occurred while executing the command.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                print(f'CONSOLE ONLY, COMMAND INVOKE ERROR: {error}')
        
        # Conversion and Parsing Errors
        elif isinstance(error, commands.ConversionError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Failed to convert the provided argument.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.PartialEmojiConversionFailure):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Failed to convert the emoji. Please use a valid emoji.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.ArgumentParsingError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Failed to parse command arguments.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.UnexpectedQuoteError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Unexpected quote character in command arguments.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.InvalidEndOfQuotedStringError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Invalid characters after quoted string.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.ExpectedClosingQuoteError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Missing closing quote in command arguments.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        # Flag Errors
        elif isinstance(error, commands.BadFlagArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Invalid flag argument provided.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.MissingFlagArgument):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Missing required flag argument.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.TooManyFlags):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Too many flags provided for this command.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.MissingRequiredFlag):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Missing required flag for this command.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        elif isinstance(error, commands.FlagError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Error with command flags.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Error technical", value=f"{error}", inline=False)
                embed.set_footer(text=BOTVERSION)
                await ctx.reply(embed=embed, mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
        
        # Extension Errors (these typically won't show to users, but included for completeness)
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            print(f'CONSOLE ONLY, EXTENSION ALREADY LOADED: {error}')
        
        elif isinstance(error, commands.ExtensionNotLoaded):
            print(f'CONSOLE ONLY, EXTENSION NOT LOADED: {error}')
        
        elif isinstance(error, commands.ExtensionNotFound):
            print(f'CONSOLE ONLY, EXTENSION NOT FOUND: {error}')
        
        elif isinstance(error, commands.NoEntryPointError):
            print(f'CONSOLE ONLY, NO ENTRY POINT: {error}')
        
        elif isinstance(error, commands.ExtensionFailed):
            print(f'CONSOLE ONLY, EXTENSION FAILED: {error}')
        
        elif isinstance(error, commands.ExtensionError):
            print(f'CONSOLE ONLY, EXTENSION ERROR: {error}')
        
        elif isinstance(error, commands.CommandRegistrationError):
            print(f'CONSOLE ONLY, COMMAND REGISTRATION ERROR: {error}')
        
        # Hybrid Command Errors
        elif isinstance(error, commands.HybridCommandError):
            if hasattr(ctx, '_ignore_'):
                pass
            else:
                embed = discord.Embed(title=f"Error description", description=f"Error with hybrid command execution.", color=0xff0000, timestamp=datetime.now(timezone.utc))
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
