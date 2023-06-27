import sys
import os
from discord.ext import commands
from configparser import ConfigParser

path = os.path.abspath(os.getcwd())
config = ConfigParser()
config.read(rf'{path}/config.ini')
owner_id = int(config['BOTCONFIG']['ownerid'])

MSG_DEL_DELAY = 10

class CogManager(commands.Cog):
    '''This Cogs module is used to load or unload different modules to update the bot without having to take it offline'''
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog loader/unloader/reloader module online')
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, name:str):
        '''Loads a module.'''
        if ctx.author.id == owner_id:
            try:
                await self.bot.load_extension(f"cogs.{name}")
            except Exception as e:
                msg = await ctx.reply(f"Error when loading module: {e}")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await msg.delete(delay=MSG_DEL_DELAY)
                return print(f"Error when loading module: {e}")
            
            msg = await ctx.reply(f"Loaded module **{name}**")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def un(self, ctx, name:str):
        '''Unloads a module.'''
        if ctx.author.id == owner_id:
            try:
                await self.bot.unload_extension(f"cogs.{name}")
            except Exception as e:
                msg = await ctx.reply(f"Error when unloading module: {e}")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await msg.delete(delay=MSG_DEL_DELAY)
                return print(f"Error when unloading module: {e}")
            
            msg = await ctx.reply(f"Unloaded module **{name}**")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def re(self, ctx, name:str):
        '''Reloads a module.'''
        if ctx.author.id == owner_id:
            try:
                await self.bot.reload_extension(f"cogs.{name}")
            except Exception as e:
                msg = await ctx.reply(f"Error when reloading module: {e}")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await msg.delete(delay=MSG_DEL_DELAY)
                return print(f"Error when reloading module: {e}")
            
            msg = await ctx.reply(f"Reloaded module **{name}**")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reall(self, ctx):
        '''Reloads all modules.'''
        if ctx.author.id == owner_id:
            msg = await ctx.send("Trying to reload all modules...")
            for filename in os.listdir(os.path.abspath(os.getcwd()) + '/cogs'):
                if filename.endswith(".py"):
                    name = filename[:-3]
                    try:
                        await self.bot.reload_extension(f"cogs.{name}")
                        await msg.edit(content=f"Reloaded module **{name}**")
                    except Exception as e:
                        msg = await ctx.reply(f"Error when reloading module: {e}")
                        await ctx.message.delete(delay=MSG_DEL_DELAY)
                        await msg.delete(delay=MSG_DEL_DELAY)
                        return print(f"Error when unloading module: {e}")
            
            await msg.edit(content="Successfully reloaded all modules")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def loadall(self, ctx):
        '''Loads all modules.'''
        if ctx.author.id == owner_id:
            msg = await ctx.send("Trying to load all modules...")
            for filename in os.listdir(os.path.abspath(os.getcwd()) + '/cogs'):
                if filename.endswith(".py"):
                    name = filename[:-3]
                    try:
                        await self.bot.load_extension(f"cogs.{name}")
                        await msg.edit(content=f"Loaded module **{name}**")
                    except Exception as e:
                        msg = await ctx.reply(f"Error when loading module: {e}")
                        await ctx.message.delete(delay=MSG_DEL_DELAY)
                        await msg.delete(delay=MSG_DEL_DELAY)
                        return print(f"Error when unloading module: {e}")
            
            await msg.edit(content="Successfully loaded all modules")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    async def stop(self, ctx):
        '''Unloads all modules.'''
        if ctx.author.id == owner_id:
            message = await ctx.send(f"Unloading modules")
            for filename in os.listdir(os.path.abspath(os.getcwd()) + '/cogs'):
                if filename.endswith(".py"):
                    name = filename[:-3]
                    try:
                        await self.bot.unload_extension(f"cogs.{name}")
                        await message.edit(content=f"Unloaded module **{name}**")
                    except Exception as e:
                        msg = await ctx.reply(f"Error when unloading module: {e}")
                        await ctx.message.delete(delay=MSG_DEL_DELAY)
                        await msg.delete(delay=MSG_DEL_DELAY)
                        print(f"Error when unloading module: {e}")
            
            await message.edit(content="Going offline, goodbye, finally at rest")
            await self.bot.close()
            sys.exit('Bot stopped manually')
        else:
            msg = await ctx.reply("Why are you trying to stop me?")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)

async def setup(bot):
    await bot.add_cog(CogManager(bot))