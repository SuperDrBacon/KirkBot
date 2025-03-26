import re
import discord

from discord.ext import commands
from datetime import datetime, timezone
from cogs.utils.constants import BOTVERSION, COMMAND_PREFIX

class ButtonHelpCommand(commands.HelpCommand):
    """
    An interactive help command implementation using Discord's UI components.
    Uses buttons for navigation and provides a paginated experience.
    """
    def __init__(self):
        super().__init__()
        self.context = None
        self.current_page = 1
        self.commands_per_page = 5
    
    async def send_bot_help(self, mapping):
        """
        Sends the main help menu with all command categories and buttons for navigation.
        """
        # Store the context for later use
        self.context = self.context  # This line seems redundant but keeping it for consistency
        
        # Create pages for categories
        all_pages = []
        cog_selection = []
        
        # Main help page
        main_embed = discord.Embed(
            title="Bot Help Menu",
            description="Welcome to the help menu! Use the buttons below to navigate.",
            color=discord.Colour.gold(),
            timestamp=datetime.now(timezone.utc))
        main_embed.set_footer(text=f"{BOTVERSION} | Page 1")
        
        # Add categories overview
        for cog_name, cog in self.context.bot.cogs.items():
            # Skip cogs with no commands or all hidden/permission-restricted commands
            commands = cog.get_commands()
            if not commands:
                continue
                
            # Filter commands by permissions and hidden status
            filtered = await self.filter_commands(commands, sort=True)
            if not filtered:
                continue
                
            # Add to cog selection for dropdown
            cog_selection.append(discord.SelectOption(
                label=cog_name,
                description=getattr(cog, "description", "Commands category")[:100]))
            
            # Add summary to main page
            visible_commands = len([cmd for cmd in filtered if not cmd.hidden])
            main_embed.add_field(
                name=f"{cog_name} [{visible_commands} commands]",
                value=getattr(cog, "description", "No description available.")[:100] + "...",
                inline=False)
            
        all_pages.append(main_embed)
        
        # Create individual cog pages - only for cogs with visible commands
        for cog_name, cog in self.context.bot.cogs.items():
            commands = cog.get_commands()
            filtered = await self.filter_commands(commands, sort=True)
            
            if not filtered:
                continue
                
            cog_embed = discord.Embed(
                title=f"{cog_name} Commands",
                description=getattr(cog, "description", "No description available."),
                color=discord.Colour.gold(),
                timestamp=datetime.now(timezone.utc))
            
            # Add commands to page
            regular_commands = []
            group_commands = []
            
            # First separate regular commands from groups
            for command in filtered:
                if command.hidden:
                    continue
                if isinstance(command, commands.Group):
                    group_commands.append(command)
                else:
                    regular_commands.append(command)
            
            # Add regular commands
            for command in regular_commands:
                signature = command.signature or ""
                cog_embed.add_field(
                    name=f"{COMMAND_PREFIX}{command.name} {signature}",
                    value=command.help or "No description available.",
                    inline=False)
            
            # Add group commands with their subcommands
            for group in group_commands:
                signature = group.signature or ""
                
                # Get filtered subcommands
                subcommands = await self.filter_commands(group.commands, sort=True)
                subcommand_list = ""
                
                for subcmd in subcommands:
                    if not subcmd.hidden:
                        subcommand_list += f"\n• `{COMMAND_PREFIX}{group.name} {subcmd.name}` - {subcmd.short_doc or 'No description'}"
                
                cog_embed.add_field(
                    name=f"{COMMAND_PREFIX}{group.name} {signature} [Group]",
                    value=f"{group.help or 'No description available.'}\n\n**Available Subcommands:**{subcommand_list or ' None'}",
                    inline=False)
            
            all_pages.append(cog_embed)
        
        # Setup the view with navigation buttons
        view = HelpView(self.context, all_pages, cog_selection)
        message = await self.get_destination().send(embed=all_pages[0], view=view)
        view.message = message

    async def send_command_help(self, command):
        """
        Displays help for a specific command.
        """
        embed = discord.Embed(
            title=f"Command: {command.qualified_name}",
            description=command.help or "No description available.",
            color=discord.Colour.gold(),
            timestamp=datetime.now(timezone.utc))
        
        # Command signature
        if command.signature:
            clean_signature = re.sub(r'=[^\]]+(?=\])', '', command.signature)
            embed.add_field(
                name="Usage",
                value=f"{COMMAND_PREFIX}{command.qualified_name} {clean_signature}",
                inline=False)
            embed.add_field(
                name="Format Guide",
                value="<argument> - Required argument\n[argument] - Optional argument",
                inline=False)
        
        # Command aliases
        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join([f"{COMMAND_PREFIX}{alias}" for alias in command.aliases]),
                inline=False)
        
        # Info about parent if this is a subcommand
        if command.parent:
            embed.add_field(
                name="Parent Command",
                value=f"{COMMAND_PREFIX}{command.parent.qualified_name}",
                inline=False)
        
        embed.set_footer(text=BOTVERSION)
        
        view = BackButtonView(self.context)
        message = await self.get_destination().send(embed=embed, view=view)
        view.message = message

    async def send_group_help(self, group):
        """
        Displays help for a command group with its subcommands.
        """
        embed = discord.Embed(
            title=f"Command Group: {group.qualified_name}",
            description=group.help or "No description available.",
            color=discord.Colour.gold(),
            timestamp=datetime.now(timezone.utc))
        
        # Group usage
        if group.signature:
            clean_signature = re.sub(r'=[^\]]+(?=\])', '', group.signature)
            embed.add_field(
                name="Usage",
                value=f"{COMMAND_PREFIX}{group.qualified_name} {clean_signature}",
                inline=False)
        
        # Subcommands
        filtered = await self.filter_commands(group.commands, sort=True)
        if filtered:
            for command in filtered:
                signature = command.signature or ""
                embed.add_field(
                    name=f"{COMMAND_PREFIX}{command.qualified_name} {signature}",
                    value=command.help or "No description available.",
                    inline=False)
        
        embed.set_footer(text=BOTVERSION)
        
        view = BackButtonView(self.context)
        message = await self.get_destination().send(embed=embed, view=view)
        view.message = message

    async def send_cog_help(self, cog):
        """
        Displays help for all commands in a cog.
        """
        embed = discord.Embed(
            title=f"Module: {cog.qualified_name}",
            description=cog.description or "No description available.",
            color=discord.Colour.gold(),
            timestamp=datetime.now(timezone.utc))
        
        commands = cog.get_commands()
        filtered = await self.filter_commands(commands, sort=True)
        
        if filtered:
            # First, separate regular commands from group commands for better organization
            regular_commands = []
            group_commands = []
            
            for command in filtered:
                if command.hidden:
                    continue
                    
                if isinstance(command, commands.Group):
                    group_commands.append(command)
                else:
                    regular_commands.append(command)
            
            # Add regular commands first
            for command in regular_commands:
                signature = command.signature or ""
                embed.add_field(
                    name=f"{COMMAND_PREFIX}{command.name} {signature}",
                    value=command.help or "No description available.",
                    inline=False)
            
            # Then add group commands with their subcommands
            for group in group_commands:
                signature = group.signature or ""
                
                # Get accessible subcommands
                subcommands = await self.filter_commands(group.commands, sort=True)
                
                # Create a formatted list of subcommands
                subcommand_list = ""
                for subcmd in subcommands:
                    subcommand_list += f"\n• `{COMMAND_PREFIX}{group.name} {subcmd.name}` - {subcmd.short_doc or 'No description'}"
                
                # Add the group command with its subcommands
                embed.add_field(
                    name=f"{COMMAND_PREFIX}{group.name} {signature} [Group]",
                    value=f"{group.help or 'No description available.'}\n\n**Available Subcommands:**{subcommand_list or ' None'}",
                    inline=False)
        
        embed.set_footer(text=BOTVERSION)
        
        view = BackButtonView(self.context)
        message = await self.get_destination().send(embed=embed, view=view)
        view.message = message


class HelpView(discord.ui.View):
    """
    View for navigating help pages with buttons.
    """
    def __init__(self, ctx, pages, cog_options):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.pages = pages
        self.current_page = 0
        self.total_pages = len(pages)
        self.message = None
        
        # Add cog selection dropdown if we have options
        if cog_options:
            self.add_item(CogSelect(cog_options))
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page - 1) % self.total_pages
        embed = self.pages[self.current_page]
        embed.set_footer(text=f"{BOTVERSION} | Page {self.current_page + 1}/{self.total_pages}")
        await interaction.response.edit_message(embed=embed)
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji="➡️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page + 1) % self.total_pages
        embed = self.pages[self.current_page]
        embed.set_footer(text=f"{BOTVERSION} | Page {self.current_page + 1}/{self.total_pages}")
        await interaction.response.edit_message(embed=embed)
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="✖️")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.message.delete()
        self.stop()
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This help menu is not for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        
        try:
            await self.message.edit(view=self)
        except:
            pass

class CogSelect(discord.ui.Select):
    """
    Dropdown for selecting different command categories.
    """
    def __init__(self, options):
        super().__init__(
            placeholder="Select a module...",
            min_values=1,
            max_values=1,
            options=options)
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        selected_cog_name = self.values[0]
        
        # Find the page index with this cog
        for i, page in enumerate(view.pages):
            if hasattr(page, 'title') and page.title == f"{selected_cog_name} Commands":
                view.current_page = i
                break
        
        # Update the page
        embed = view.pages[view.current_page]
        embed.set_footer(text=f"{BOTVERSION} | Page {view.current_page + 1}/{view.total_pages}")
        await interaction.response.edit_message(embed=embed)

class BackButtonView(discord.ui.View):
    """
    Simple view with just a back button for command/group help pages.
    """
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.message = None
    
    @discord.ui.button(label="Back to Help Menu", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.message.delete()
        
        # Invoke the help command again to go back to the main menu
        await self.ctx.send_help()
        self.stop()
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="✖️")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.message.delete()
        self.stop()
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This help menu is not for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        
        try:
            await self.message.edit(view=self)
        except:
            pass

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
        
        embed = discord.Embed(title="All Commands", color=discord.Colour.gold(), timestamp=datetime.now(timezone.utc))
        
        for cog, commands in mapping.items():
            if cog is None:
                continue
            cog_name = cog.qualified_name
            commands = await self.filter_commands(commands, sort=False)
            
            if commands:
                command_names = [f'{COMMAND_PREFIX}{command.name}' for command in commands if not command.hidden]
                formatted_command_names = '\n'.join(command_names)
                embed.add_field(name=cog_name, value=formatted_command_names, inline=True)
        
        embed.add_field(name="―――――――――――――――――――", value=f"Run {COMMAND_PREFIX}{self.invoked_with} [module] to learn more about a module and its commands\nRun {COMMAND_PREFIX}{self.invoked_with} [command] to learn more about a command", inline=False)
        embed.set_footer(text=BOTVERSION)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        '''
        Sends a help message containing all available commands for a specific group.
        
        Parameters:
            group (commands.Group): The group to get the commands for.
            
        Returns:
            None
        '''
        embed = discord.Embed(title=f"Group: {group.name}", description=group.description or "All commands related to this group", color=discord.Colour.gold(), timestamp=datetime.now(timezone.utc))
        
        if group.help:
            embed.add_field(name="Help", value=group.help, inline=False)
        
        for command in group.commands:
            if not command.hidden:
                embed.add_field(name=f'{COMMAND_PREFIX}{group.name} {command.name}', value=command.help or "No description available.", inline=False)
        
        embed.set_footer(text=BOTVERSION)
        await self.get_destination().send(embed=embed)


    async def send_command_help(self, cmd):
        '''
        Sends a help message containing information about a specific command.
        
        Parameters:
            cmd (commands.Command): The command to get help for.
            
        Returns:
            None
        '''
        embed = discord.Embed(title=f"Command: {cmd.name}", description=cmd.help or "No description available.", color=discord.Colour.gold(), timestamp=datetime.now(timezone.utc))
        
        if cmd.usage:
            embed.add_field(name="Usage", value=f"{COMMAND_PREFIX}{cmd.name} {cmd.usage}", inline=False)
        
        if cmd.aliases:
            embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
        
        if cmd.signature:
            argument_text = "\n< > is a <required> argument.\n[ ] is an [optional] argument."
            clean_signature = re.sub(r'=[^\]]+(?=\])', '', cmd.signature)
        else:
            no_argument_text = "\nThis command has no extra arguments."
            clean_signature = ""
        embed.add_field(name="Usage", value=f"{COMMAND_PREFIX}{' '.join(self.context.message.content.split(' ')[1:]) or cmd.name} {clean_signature}{argument_text if cmd.signature else no_argument_text}", inline=False)
        embed.set_footer(text=BOTVERSION)
        await self.get_destination().send(embed=embed)


    async def send_cog_help(self, cog):
        '''
        Sends a help message containing all available commands for a specific cog.
        
        Parameters:
            cog (commands.Cog): The cog to get the commands for.
            
        Returns:
            None
        '''
        embed = discord.Embed(title=f"Module: {cog.qualified_name}", description=cog.description or "No description available.", color=discord.Colour.gold(), timestamp=datetime.now(timezone.utc))
        
        for command in cog.get_commands():
            if not command.hidden:
                aliases = [''.join(''.join(alias) for alias in cmd_aliases) for cmd_aliases in command.aliases]
                embed.add_field(name=command.name, value=f"{'No ALias.' if len(aliases) == 0 else ('Alias:' if len(aliases) == 1 else 'Aliases:')} {', '.join(aliases)}\n{command.help or 'No description available.'}", inline=True)
        
        embed.add_field(name="―――――――――――――――――――", value=f"Run {COMMAND_PREFIX}{self.invoked_with} [command] to learn more about a command", inline=False)
        embed.set_footer(text=BOTVERSION)
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