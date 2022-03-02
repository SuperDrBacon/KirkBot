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
        for filename in os.listdir(os.path.abspath(os.getcwd()) + '\\cogs'):
            if filename.endswith(".py"):
                name = filename[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                    await ctx.send(f"Reloaded module **{name}**")
                except Exception as e:
                    await ctx.send(f"The following module failed...\n\n{e}")
        await ctx.send("Successfully reloaded all modules")
        
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def loadall(self, ctx):
        '''Loads all modules.'''
        for filename in os.listdir(os.path.abspath(os.getcwd()) + '\\cogs'):
            if filename.endswith(".py"):
                name = filename[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                    await ctx.send(f"Loaded module **{name}**")
                except Exception as e:
                    await ctx.send(f"The following module failed...\n\n{e}")
        await ctx.send("Successfully loaded all modules")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stop(self, ctx):
        '''Unloads all modules.'''
        message = await ctx.send(f"Unloading modules")
        for filename in os.listdir(os.path.abspath(os.getcwd()) + '\\cogs'):
            if filename.endswith(".py"):
                name = filename[:-3]
                try:
                    self.bot.unload_extension(f"cogs.{name}")
                    await message.edit(content=f"unloaded module **{name}**")
                except Exception as e:
                    await ctx.send(f"The following module failed...\n\n{e}")
        await message.edit("Going offline, goodbye : (")
        exit()


def setup(bot):
    bot.add_cog(Cogs(bot))