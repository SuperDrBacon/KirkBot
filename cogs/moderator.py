import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import CheckFailure



class ModCommands(commands.Cog):
    '''
    This module houses all the moderation commands.
    '''
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
            print('moderator module online')


    # @commands.command(name='purge')
    # @commands.has_permissions(manage_messages=True)
    # async def purge(self, ctx, amount=0):
    #     # await ctx.message.delete()

    #     if amount == 0:
    #         await ctx.send("You didn't specify a purge amount.")
    #         await asyncio.sleep(1)
    #         await ctx.channel.purge(limit = 1)

    #     if amount >= 1:
    #         await ctx.channel.purge(limit = amount + 1)
        
    #     if amount < 0:
    #         await ctx.send('you just tried to delete a negative amount of messages. are you braindumb')
    #         await asyncio.sleep(1)
    #         await ctx.channel.purge(limit = 1)
    # @purge.error
    # async def purge_error(self, ctx, error):
    #     if isinstance(error, CheckFailure):
    #         await ctx.send("No permissions to purge")

    
    # @commands.command()
    # async def kick(self, ctx, member : discord.Member, *, reason=None):
    #     if not reason:
    #         await member.kick(f'{discord.Member} was kicked without reason.')
        
    #     if reason:
    #         await member.kick(f'{discord.Member} was kicked with the reason {reason}')
            
            
            
    # @commands.command()
    # @commands.command()
    # @commands.command()
    # @commands.command()
    # @commands.command()
    # @commands.command()






async def setup(bot):
    await bot.add_cog(ModCommands(bot))