import discord
import os
from discord.ext import commands

class Cogs(commands.Cog):
    '''This Cogs module is used to load or unload different modules to update the bot without having to take it offline'''
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
            print('Cog loader/unloader/reloader module online')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, name: str):
        '''Loads a module.'''
        try:
            self.bot.load_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(f"Error when loading cog: {e}")
        await ctx.send(f"Loaded module **{name}**")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def un(self, ctx, name: str):
        '''Unloads a module.'''
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(f"Error when unloading cog: {e}")
        await ctx.send(f"Unloaded module **{name}**")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def re(self, ctx, name: str):
        '''Reloads a module.'''
        try:
            self.bot.reload_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(f"Error when reloading cog: {e}")
        await ctx.send(f"Reloaded module **{name}**")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reall(self, ctx):
        '''Reloads all modules.'''
        error_collection = []
        for filename in os.listdir('./KirkBot/cogs'):
            if filename.endswith(".py"):
                name = filename[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                    await ctx.send(f"Reloaded module **{name}**")
                except Exception as e:
                    error_collection.append(filename, e)

        if error_collection:
            output = "\n".join([f"**{g[0]}** ```diff\n- {g[1]}```" for g in error_collection])
            return await ctx.send(
                f"Attempted to reload all extensions, was able to reload, "
                f"however the following failed...\n\n{output}"
            )

        await ctx.send("Successfully reloaded all extensions")

def setup(bot):
    bot.add_cog(Cogs(bot))