import datetime
import os
import re
import discord
import cogs.utils.functions as functions
from discord import Embed
from discord.ext import commands
from configparser import ConfigParser


path = os.path.abspath(os.getcwd())
info, config = ConfigParser(), ConfigParser()
info.read(rf'{path}/info.ini')
config.read(rf'{path}/config.ini')

prefix = config['BOTCONFIG']['prefix']
botversion = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']
timestamp = datetime.datetime.now()

class NewHelpCommand(commands.HelpCommand):
    '''
    A custom help command class that extends the default help command of discord.py.
    This class provides methods to send help messages containing information about the bot's commands, groups, and cogs.
    '''
    def __init__(self):
        super().__init__()
    
    async def send_bot_help(self, mapping):
        '''
        Sends a help message containing all available commands for the bot.
        
        Parameters:
            mapping (dict): A dictionary containing all the bot's cogs and their associated commands.
            
        Returns:
            None
        '''
        
        embed = Embed(title="All Commands", color=discord.Colour.gold(), timestamp=timestamp)
        
        for cog, commands in mapping.items():
            if cog is None:
                continue
            cog_name = cog.qualified_name
            commands = await self.filter_commands(commands, sort=False)
            
            if commands:
                command_names = [f'{prefix}{command.name}' for command in commands if not command.hidden]
                formatted_command_names = '\n'.join(command_names)
                embed.add_field(name=cog_name, value=formatted_command_names, inline=True)
        
        embed.add_field(name="―――――――――――――――――――", value=f"Run {prefix}{self.invoked_with} [module] to learn more about a module and its commands\nRun {prefix}{self.invoked_with} [command] to learn more about a command", inline=False)
        embed.set_footer(text=botversion)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        '''
        Sends a help message containing all available commands for a specific group.
        
        Parameters:
            group (commands.Group): The group to get the commands for.
            
        Returns:
            None
        '''
        embed = Embed(title=f"Group: {group.name}", description=group.description or "No description available.", color=discord.Colour.gold(), timestamp=timestamp)
        
        if group.help:
            embed.add_field(name="Help", value=group.help, inline=False)
        
        for command in group.commands:
            if not command.hidden:
                embed.add_field(name=command.name, value=command.help or "No description available.", inline=False)
        
        embed.set_footer(text=botversion)
        await self.get_destination().send(embed=embed)


    async def send_command_help(self, cmd):
        '''
        Sends a help message containing information about a specific command.
        
        Parameters:
            cmd (commands.Command): The command to get help for.
            
        Returns:
            None
        '''
        embed = Embed(title=f"Command: {cmd.name}", description=cmd.help or "No description available.", color=discord.Colour.gold(), timestamp=timestamp)
        
        if cmd.usage:
            embed.add_field(name="Usage", value=f"{prefix}{cmd.name} {cmd.usage}", inline=False)
        
        if cmd.aliases:
            embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
        
        if cmd.signature:
            argument_text = "\n< > is a <required> argument.\n[ ] is an [optional] argument."
            clean_signature = re.sub(r'=\d+', '', cmd.signature)
        else:
            no_argument_text = "\nThis command has no extra arguments."
            clean_signature = ""
        embed.add_field(name="Usage", value=f"{prefix}{cmd.name} {clean_signature}{argument_text if cmd.signature else no_argument_text}", inline=False)
        
        embed.set_footer(text=botversion)
        await self.get_destination().send(embed=embed)


    async def send_cog_help(self, cog):
        '''
        Sends a help message containing all available commands for a specific cog.
        
        Parameters:
            cog (commands.Cog): The cog to get the commands for.
            
        Returns:
            None
        '''
        embed = Embed(title=f"Module: {cog.qualified_name}", description=cog.description or "No description available.", color=discord.Colour.gold(), timestamp=timestamp)
        
        for command in cog.get_commands():
            if not command.hidden:
                aliases = [''.join(''.join(alias) for alias in cmd_aliases) for cmd_aliases in command.aliases]
                embed.add_field(name=command.name, value=f"{'No ALias.' if len(aliases) == 0 else ('Alias:' if len(aliases) == 1 else 'Aliases:')} {', '.join(aliases)}\n{command.help or 'No description available.'}", inline=True)
        
        embed.add_field(name="―――――――――――――――――――", value=f"Run {prefix}{self.invoked_with} [command] to learn more about a command", inline=False)
        embed.set_footer(text=botversion)
        await self.get_destination().send(embed=embed)
        
        
    # async def send_command_help(self, cmd):
    #     desc = \
    #     f"name: {cmd.name}\ncog: {cmd.cog_name}\ndescription:\n {cmd.help or cmd.short_doc}\n\n" \
    #     f"aliases:\n - {', '.join(cmd.aliases) if cmd.aliases else 'None'}\n\n" \
    #     f"usage: {cmd.name} {cmd.signature}"

    #     embed = discord.Embed(title=f"Command info: {cmd.qualified_name}")
    #     embed.description = f"```yaml\n---\n{desc}\n---\n```"
    #     embed.set_footer(text="[optional], <required>, = denotes default value")
    #     await self.get_destination().send(embed=embed)

