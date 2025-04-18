import importlib
import os
import sys
import pkgutil
import inspect
import git

from discord.ext import commands
from cogs.utils.constants import MSG_DEL_DELAY, OSPATH, OWNER_ID

def reload_module_recursive(module_name):
    r"""
    Recursively reload a module and all its submodules.
    
    Args:
        module_name (str): The name of the module to reload
    
    Returns:
        list: Names of all reloaded modules
    """
    reloaded = []
    
    # If it's not loaded yet, just return
    if module_name not in sys.modules:
        return reloaded
    
    # Get the module object
    module = sys.modules[module_name]
    
    # Reload the module itself
    importlib.reload(module)
    reloaded.append(module_name)
    
    # If it's a package, reload all submodules
    if hasattr(module, '__path__'):
        # Get all submodules recursively
        for _, submodule_name, is_pkg in pkgutil.walk_packages(module.__path__, module.__name__ + '.'):
            if submodule_name in sys.modules:
                importlib.reload(sys.modules[submodule_name])
                reloaded.append(submodule_name)
    
    # Also reload any modules that were imported from this module
    for name, obj in inspect.getmembers(module):
        if inspect.ismodule(obj) and obj.__name__ not in reloaded and obj.__name__ in sys.modules:
            sub_reloaded = reload_module_recursive(obj.__name__)
            reloaded.extend(sub_reloaded)
    return reloaded

class BotMechanics(commands.Cog):
    '''This module is used to load or unload different modules to update the bot without having to take it offline'''
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog loader/unloader/reloader module online')
    
    @commands.command(aliases=["update"], hidden=True)
    async def update_bot(self, ctx):
        '''
        Update the bot's code from the remote repository and report the number of commits behind and ahead. 
        If the bot is already up to date, no action is taken. 
        This command is hidden and can only be used by the bot owner.
        '''
        if ctx.author.id == OWNER_ID:
            repo = git.Repo(OSPATH)
            repo.remotes.origin.fetch()
            commits_behind = len(list(repo.iter_commits('master..origin/master')))
            commits_ahead = len(list(repo.iter_commits('origin/master..master')))
            await ctx.send(f'{commits_behind} commits behind, {commits_ahead} commits ahead', delete_after=MSG_DEL_DELAY)
            
            if commits_behind > 0 and commits_ahead > 0:
                repo.remotes.origin.push()
                repo.remotes.origin.pull()
                await ctx.send('KirBot local and remote updated', delete_after=MSG_DEL_DELAY)
            elif commits_behind > 0:
                repo.remotes.origin.pull()
                await ctx.send('KirBot local updated', delete_after=MSG_DEL_DELAY)	
            elif commits_ahead > 0:
                repo.remotes.origin.push()
                await ctx.send('KirBot remote updated', delete_after=MSG_DEL_DELAY)
            else:
                await ctx.send('KirkBot is already up to date with the remote', delete_after=MSG_DEL_DELAY)
        await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, name:str):
        '''Loads a module.'''
        if ctx.author.id == OWNER_ID:
            try:
                await self.bot.load_extension(f"cogs.{name}")
            except Exception as e:
                await ctx.reply(f"Error when loading module: {e}", mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                return print(f"Error when loading module: {e}")
            
            await ctx.reply(f"Loaded module **{name}**", mention_author=False, delete_after=MSG_DEL_DELAY)
            await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def un(self, ctx, name:str):
        '''Unloads a module.'''
        if ctx.author.id == OWNER_ID:
            try:
                await self.bot.unload_extension(f"cogs.{name}")
            except Exception as e:
                await ctx.reply(f"Error when unloading module: {e}", mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                return print(f"Error when unloading module: {e}")
            
            await ctx.reply(f"Unloaded module **{name}**", mention_author=False, delete_after=MSG_DEL_DELAY)
            await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def re(self, ctx, name:str):
        '''Reloads a module and its dependencies.'''
        if ctx.author.id == OWNER_ID:
            try:
                response = f"Reloaded module **{name}**"
                
                # Recursively reload utility and game modules
                if name == "econ":
                    reloaded_games = reload_module_recursive("cogs.games")
                    response += f" + {len(reloaded_games)} game modules"
                
                reloaded_utils = reload_module_recursive("cogs.utils")
                response += f" + {len(reloaded_utils)} utility modules"
                
                # Standard extension reload
                await self.bot.reload_extension(f"cogs.{name}")
            
            except Exception as e:
                await ctx.reply(f"Error when reloading module: {e}", mention_author=False, delete_after=MSG_DEL_DELAY)
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                return print(f"Error when reloading module: {e}")
            
            await ctx.reply(response, mention_author=False, delete_after=MSG_DEL_DELAY)
            await ctx.message.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reall(self, ctx):
        '''Reloads all modules and their dependencies.'''
        if ctx.author.id == OWNER_ID:
            msg = await ctx.send("Trying to reload all modules...")
            
            # recursively reload utilities and games
            await msg.edit(content="Reloading utility modules...")
            utils_reloaded = reload_module_recursive("cogs.utils")
            
            await msg.edit(content="Reloading game modules...")
            games_reloaded = reload_module_recursive("cogs.games")
            
            # reload all standard extensions
            for filename in os.listdir(rf'{OSPATH}/cogs'):
                if filename.endswith(".py"):
                    name = filename[:-3]
                    try:
                        await self.bot.reload_extension(f"cogs.{name}")
                        await msg.edit(content=f"Reloaded module **{name}**")
                    except Exception as e:
                        await ctx.reply(f"Error when reloading module: {e}", mention_author=False, delete_after=MSG_DEL_DELAY)
                        await ctx.message.delete(delay=MSG_DEL_DELAY)
                        await msg.delete(delay=MSG_DEL_DELAY)
                        return print(f"Error when reloading module: {e}")
            
            # Final message with stats
            await msg.edit(content=f"Successfully reloaded all modules, including {len(utils_reloaded)} utility modules and {len(games_reloaded)} game modules")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def loadall(self, ctx):
        '''Loads all modules.'''
        if ctx.author.id == OWNER_ID:
            msg = await ctx.send("Trying to load all modules...")
            for filename in os.listdir(rf'{OSPATH}/cogs'):
                if filename.endswith(".py"):
                    name = filename[:-3]
                    try:
                        await self.bot.load_extension(f"cogs.{name}")
                        await msg.edit(content=f"Loaded module **{name}**")
                    except Exception as e:
                        await ctx.reply(f"Error when loading module: {e}", mention_author=False, delete_after=MSG_DEL_DELAY)
                        await ctx.message.delete(delay=MSG_DEL_DELAY)
                        await msg.delete(delay=MSG_DEL_DELAY)
                        return print(f"Error when unloading module: {e}")
            
            await msg.edit(content="Successfully loaded all modules")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(hidden=True)
    async def stop(self, ctx):
        '''Unloads all modules.'''
        if ctx.author.id == OWNER_ID:
            msg = await ctx.send(f"Unloading modules")
            for filename in os.listdir(rf'{OSPATH}/cogs'):
                if filename.endswith(".py"):
                    name = filename[:-3]
                    try:
                        await self.bot.unload_extension(f"cogs.{name}")
                        await msg.edit(content=f"Unloaded module **{name}**")
                    except Exception as e:
                        await ctx.reply(f"Error when unloading module: {e}", mention_author=False, delete_after=MSG_DEL_DELAY)
                        await ctx.message.delete(delay=MSG_DEL_DELAY)
                        await msg.delete(delay=MSG_DEL_DELAY)
                        print(f"Error when unloading module: {e}")
            
            await msg.edit(content="Going offline, goodbye, finally at rest")
            await self.bot.close()
            sys.exit('Bot stopped manually')
        else:
            await ctx.reply("Why are you trying to stop me?", mention_author=False, delete_after=MSG_DEL_DELAY)
            await ctx.message.delete(delay=MSG_DEL_DELAY)

async def setup(bot):
    await bot.add_cog(BotMechanics(bot))