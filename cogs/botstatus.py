import discord
import asyncio
from discord.ext import commands

activity = discord.Activity(name='the world turn darker', type=discord.ActivityType.watching)

class setStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    
    #events
    @commands.Cog.listener()
    async def on_ready(self):
            print('status module online')
            return await self.bot.change_presence(status=discord.Status.online, activity=activity)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("command doesn't exist")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please pass in all requirements :rolling_eyes:.')
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You dont have all the requirements :angry:")

    #commands
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def status(self, ctx, *, statusmessage):
        message = await ctx.send(f"[1️⃣ for watching]. [2️⃣ for listening to.]")
        await message.add_reaction('1️⃣')
        await message.add_reaction('2️⃣')
        
        check = lambda r, u: u == ctx.author and str(r.emoji) in "1️⃣2️⃣"
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=5)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            await ctx.message.delete()
            await message.edit(content="update cancelled, timed out.")
            return
        
        if str(reaction.emoji) == "1️⃣":
            activity = discord.Activity(name=statusmessage, type=discord.ActivityType.watching)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            strstatus = 'Watching'

        elif str(reaction.emoji) == "2️⃣":
            activity = discord.Activity(name=statusmessage, type=discord.ActivityType.listening)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            strstatus = 'Listening to'
            
        else:
            await message.edit(content="Update cancelled.")
            return

        # await ctx.message.delete()
        await message.edit(content=f'Updated Status to: {strstatus} {statusmessage}')
        await message.clear_reactions()



def setup(bot):
    bot.add_cog(setStatus(bot))
