import asyncio
import re
import discord

from datetime import datetime, timezone
from discord.ext import commands
from cogs.utils.constants import BOTVERSION, COMMAND_PREFIX

TIMEOUT = 180  # 3 minutes timeout for help command

class HelpButton(discord.ui.Button):
    """A button for the help command"""
    def __init__(self, label, style, custom_id, row=None, disabled=False):
        super().__init__(
            label=label,
            style=style,
            custom_id=custom_id,
            row=row,
            disabled=disabled
        )

class HelpView(discord.ui.View):
    """A view containing buttons for the help command navigation"""
    def __init__(self, timeout=TIMEOUT):
        super().__init__(timeout=timeout)
        self.message = None
        self.original_author = None  # Store the original command author
        self.invoking_message = None  # Store the original command message

    async def interaction_check(self, interaction):
        """Only allow the original command author to interact with these buttons"""
        if interaction.user.id == self.original_author.id:
            # Reset the timeout timer when a valid user interacts with the view
            return True
        
        # Tell other users they can't interact with this help command
        await interaction.response.send_message(
            f"Only {self.original_author.display_name} can interact with this help command.", 
            ephemeral=True
        )
        return False

    async def on_timeout(self):
        """Handle timeout by attempting to delete the help message and the invoking command"""
        # Try to delete the help message
        if self.message is not None:
            try:
                await self.message.delete()
            except (discord.errors.NotFound, discord.errors.Forbidden, Exception):
                # If we can't delete it, try to disable buttons instead
                try:
                    for item in self.children:
                        item.disabled = True
                    
                    # Update the message to show it's timed out
                    embed = self.message.embeds[0]
                    embed.set_footer(text=f"{embed.footer.text} | Timed out")
                    await self.message.edit(embed=embed, view=self)
                except Exception:
                    # If editing also fails, just silently handle the error
                    pass
        
        # Try to delete the original command message
        if self.invoking_message is not None:
            try:
                await self.invoking_message.delete()
            except (discord.errors.NotFound, discord.errors.Forbidden, Exception):
                # Silently handle any errors when trying to delete the original message
                pass

class MainHelpView(HelpView):
    """The main help view showing all modules"""
    def __init__(self, help_command, mapping, timeout=TIMEOUT):
        super().__init__(timeout=timeout)
        self.help_command = help_command
        self.mapping = mapping
        self.cogs_list = []
        self.current_page = 0
        self.buttons_per_page = 24  # 25 total buttons max (24 + 1 or 23 + 2)
        
        # Create a list of cogs that have commands
        for cog, commands in mapping.items():
            if cog is None:
                continue
            filtered_commands = [cmd for cmd in commands if not cmd.hidden]
            if filtered_commands:
                self.cogs_list.append(cog)
        
        self.total_pages = (len(self.cogs_list) + self.buttons_per_page - 1) // self.buttons_per_page
        
        # Update the view with buttons for the current page
        self.update_buttons()
    
    def update_buttons(self):
        """Update the view with buttons for the current page"""
        # Clear existing buttons
        self.clear_items()
        
        # Calculate start and end indices for the current page
        start_idx = self.current_page * self.buttons_per_page
        end_idx = min(start_idx + self.buttons_per_page, len(self.cogs_list))
        
        # Add the cog buttons for the current page
        for i, cog_idx in enumerate(range(start_idx, end_idx), 1):
            # Calculate the row based on position (5 buttons per row)
            row = (i - 1) // 5
            
            button = HelpButton(
                label=f"{cog_idx + 1}",
                style=discord.ButtonStyle.primary,
                custom_id=f"cog_{cog_idx}",
                row=row
            )
            button.callback = self.make_cog_callback(cog_idx)
            self.add_item(button)
        
        # Add pagination buttons if needed
        if self.total_pages > 1:
            # Add buttons to the last row
            pagination_row = min(4, (end_idx - start_idx - 1) // 5 + 1)
            
            # Previous page button
            prev_button = HelpButton(
                label="◀️ Previous",
                style=discord.ButtonStyle.secondary,
                custom_id="prev_page",
                row=pagination_row,
                disabled=(self.current_page == 0)
            )
            prev_button.callback = self.previous_page
            self.add_item(prev_button)
            
            # Next page button
            next_button = HelpButton(
                label="Next ▶️",
                style=discord.ButtonStyle.secondary,
                custom_id="next_page",
                row=pagination_row,
                disabled=(self.current_page == self.total_pages - 1)
            )
            next_button.callback = self.next_page
            self.add_item(next_button)
    
    async def previous_page(self, interaction):
        """Go to the previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            
            # Update the embed to reflect the current page
            embed = await self.help_command.create_bot_embed(self.mapping, self.current_page, self.buttons_per_page)
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def next_page(self, interaction):
        """Go to the next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            
            # Update the embed to reflect the current page
            embed = await self.help_command.create_bot_embed(self.mapping, self.current_page, self.buttons_per_page)
            await interaction.response.edit_message(embed=embed, view=self)

    def make_cog_callback(self, index):
        """Create a callback for a cog button"""
        async def cog_button_callback(interaction):
            if index < len(self.cogs_list):
                cog = self.cogs_list[index]
                
                # Create the cog help view
                view = CogHelpView(self.help_command, cog, self.mapping)
                view.original_author = self.original_author  # Transfer the original author reference
                
                # Create the cog help embed
                embed = await self.help_command.create_cog_embed(cog)
                
                try:
                    # Update the message with the new embed and view
                    await interaction.response.edit_message(embed=embed, view=view)
                    
                    # Make sure to store the message reference properly
                    try:
                        # For regular messages, interaction.message should work
                        view.message = interaction.message
                    except:
                        # For ephemeral or other special messages, try to get the original response
                        try:
                            view.message = await interaction.original_response()
                        except:
                            # If all else fails, at least we tried
                            pass
                except Exception:
                    # If edit fails, silently handle the error
                    pass
        
        return cog_button_callback


class CogHelpView(HelpView):
    """A view showing commands in a specific cog/module"""
    def __init__(self, help_command, cog, mapping, timeout=TIMEOUT):
        super().__init__(timeout=timeout)
        self.help_command = help_command
        self.cog = cog
        self.mapping = mapping
        self.commands_list = []
        self.current_page = 0
        self.buttons_per_page = 23  # 24 buttons + 1 back button or 22 + 3 buttons (prev, back, next)
        
        # Create a list of commands in this cog
        for command in cog.get_commands():
            if not command.hidden:
                self.commands_list.append(command)
        
        self.total_pages = (len(self.commands_list) + self.buttons_per_page - 1) // self.buttons_per_page
        
        # Update the view with buttons for the current page
        self.update_buttons()
    
    def update_buttons(self):
        """Update the view with buttons for the current page"""
        # Clear existing buttons
        self.clear_items()
        
        # Calculate start and end indices for the current page
        start_idx = self.current_page * self.buttons_per_page
        end_idx = min(start_idx + self.buttons_per_page, len(self.commands_list))
        
        # Add command buttons for the current page
        for i, cmd_idx in enumerate(range(start_idx, end_idx), 1):
            # Calculate the row (5 buttons per row, up to 4 rows for commands)
            row = min(3, (i - 1) // 5)
            
            button = HelpButton(
                label=f"{cmd_idx + 1}",
                style=discord.ButtonStyle.primary,
                custom_id=f"cmd_{cmd_idx}",
                row=row
            )
            button.callback = self.make_command_callback(cmd_idx)
            self.add_item(button)
        
        # Last row is always for navigation buttons
        navigation_row = 4
        
        # Add pagination buttons if needed
        if self.total_pages > 1:
            # Previous page button
            prev_button = HelpButton(
                label="◀️ Previous",
                style=discord.ButtonStyle.secondary,
                custom_id="prev_page",
                row=navigation_row,
                disabled=(self.current_page == 0)
            )
            prev_button.callback = self.previous_page
            self.add_item(prev_button)
        
        # Always add back button (centered if no pagination)
        back_button = HelpButton(
            label="Back",
            style=discord.ButtonStyle.danger,
            custom_id="back_to_main",
            row=navigation_row
        )
        back_button.callback = self.back_to_main
        self.add_item(back_button)
        
        if self.total_pages > 1:
            # Next page button
            next_button = HelpButton(
                label="Next ▶️",
                style=discord.ButtonStyle.secondary,
                custom_id="next_page",
                row=navigation_row,
                disabled=(self.current_page == self.total_pages - 1)
            )
            next_button.callback = self.next_page
            self.add_item(next_button)
    
    async def previous_page(self, interaction):
        """Go to the previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            
            # Update the embed to reflect the current page
            embed = await self.help_command.create_cog_embed(self.cog, self.current_page, self.buttons_per_page)
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def next_page(self, interaction):
        """Go to the next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            
            # Update the embed to reflect the current page
            embed = await self.help_command.create_cog_embed(self.cog, self.current_page, self.buttons_per_page)
            await interaction.response.edit_message(embed=embed, view=self)

    def make_command_callback(self, index):
        """Create a callback for a command button"""
        async def command_button_callback(interaction):
            if index < len(self.commands_list):
                command = self.commands_list[index]
                
                # Check if this is a command group
                if isinstance(command, commands.Group):
                    # For command groups, create an embed that shows all subcommands
                    embed = discord.Embed(
                        title=f"Group: {command.name}", 
                        description=command.description or "All commands related to this group",
                        color=discord.Colour.gold(), 
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    embed.add_field(
                        name=f"1  {COMMAND_PREFIX}{command.name}",
                        value=f"\n{command.help or 'No description available.'}",
                        inline=False
                    )
                    
                    # Add all subcommands with indices (starting from 2)
                    for idx, subcmd in enumerate(command.commands, 2):
                        if not subcmd.hidden:
                            embed.add_field(
                                name=f"{idx}  {COMMAND_PREFIX}{command.name} {subcmd.name}", 
                                value=subcmd.help or "No description available.", 
                                inline=False
                            )
                    
                    # Use GroupHelpView for Group handling
                    view = GroupHelpView(self.help_command, command, self.cog, self.mapping)
                    view.original_author = self.original_author
                    view.invoking_message = self.invoking_message
                    
                    # Update footer
                    embed.set_footer(text=BOTVERSION)
                    
                else:
                    # Regular command handling (unchanged)
                    view = CommandHelpView(self.help_command, command, self.cog, self.mapping)
                    view.original_author = self.original_author
                    view.invoking_message = self.invoking_message
                    embed = await self.help_command.create_command_embed(command)
                
                try:
                    # Update the message with the new embed and view
                    await interaction.response.edit_message(embed=embed, view=view)
                    
                    # Make sure to store the message reference properly
                    try:
                        view.message = interaction.message
                    except:
                        try:
                            view.message = await interaction.original_response()
                        except:
                            # If all else fails, at least we tried
                            pass
                except Exception:
                    # If edit fails, silently handle the error
                    pass
                
        return command_button_callback
    
    async def back_to_main(self, interaction):
        # Create the main help view again
        view = MainHelpView(self.help_command, self.mapping)
        view.original_author = self.original_author  # Transfer the original author reference
        
        # Create the main help embed
        embed = await self.help_command.create_bot_embed(self.mapping)
        
        try:
            # Update the message with the main view again
            await interaction.response.edit_message(embed=embed, view=view)
            
            # Make sure to store the message reference properly
            try:
                view.message = interaction.message
            except:
                try:
                    view.message = await interaction.original_response()
                except:
                    # If all else fails, at least we tried
                    pass
        except Exception:
            # If edit fails, silently handle the error
            pass


class GroupHelpView(HelpView):
    """A view showing a command group and its subcommands with navigation buttons"""
    def __init__(self, help_command, group, cog, mapping, timeout=TIMEOUT):
        super().__init__(timeout=timeout)
        self.help_command = help_command
        self.group = group
        self.cog = cog
        self.mapping = mapping
        self.all_commands = []
        
        # Add the base command as the first item
        self.all_commands.append(self.group)  # Base command is at index 0
        
        # Create a list of subcommands in this group
        for command in group.commands:
            if not command.hidden:
                self.all_commands.append(command)
        
        # Add buttons for the base command and each subcommand
        self.update_buttons()
    
    def update_buttons(self):
        """Add navigation buttons for each command"""
        # Clear any existing buttons
        self.clear_items()
        
        # Add button for the base command (as #1) and each subcommand
        for i, command in enumerate(self.all_commands, 1):
            # Use multiple rows if there are many commands
            row = 0 if i <= 5 else (1 if i <= 10 else 2)
            
            # Only add up to 15 command buttons to avoid overcrowding
            if i <= 15:
                button = HelpButton(
                    label=f"{i}",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"cmd_{i-1}",
                    row=row
                )
                button.callback = self.make_command_callback(i-1)
                self.add_item(button)
        
        # Add back button on the last row
        back_button = HelpButton(
            label="Back",
            style=discord.ButtonStyle.danger,
            custom_id="back_button",
            row=3
        )
        back_button.callback = self.back_to_parent
        self.add_item(back_button)
    
    def make_command_callback(self, index):
        """Create a callback for a command button"""
        async def command_button_callback(interaction):
            if index < len(self.all_commands):
                command = self.all_commands[index]
                
                # Create the command help embed
                embed = await self.help_command.create_command_embed(command)
                
                # Use CommandHelpView for the command
                view = CommandHelpView(self.help_command, command, self.cog, self.mapping, parent_view="group")
                view.original_author = self.original_author
                view.invoking_message = self.invoking_message
                view.parent_group = self.group
                
                try:
                    # Update the message with the new embed and view
                    await interaction.response.edit_message(embed=embed, view=view)
                    
                    # Make sure to store the message reference properly
                    try:
                        view.message = interaction.message
                    except:
                        try:
                            view.message = await interaction.original_response()
                        except:
                            pass
                except Exception:
                    pass
        
        return command_button_callback
    
    async def back_to_parent(self, interaction):
        """Go back to parent (cog view)"""
        # Create the cog help view again
        view = CogHelpView(self.help_command, self.cog, self.mapping)
        view.original_author = self.original_author
        view.invoking_message = self.invoking_message
        
        # Create the cog help embed
        embed = await self.help_command.create_cog_embed(self.cog)
        
        try:
            # Update the message with the cog view again
            await interaction.response.edit_message(embed=embed, view=view)
            
            # Make sure to store the message reference properly
            try:
                view.message = interaction.message
            except:
                try:
                    view.message = await interaction.original_response()
                except:
                    pass
        except Exception:
            pass


class CommandHelpView(HelpView):
    """A view showing detailed info for a specific command"""
    def __init__(self, help_command, command, cog, mapping, parent_view="cog", timeout=TIMEOUT):
        super().__init__(timeout=timeout)
        self.help_command = help_command
        self.command = command
        self.cog = cog
        self.mapping = mapping
        self.parent_view = parent_view  # Track if we came from a cog or group view
        self.parent_group = None  # Store reference to parent group if applicable
        
        # Add back button
        back_button = HelpButton(
            label="Back",
            style=discord.ButtonStyle.danger,
            custom_id="back_button",
            row=0
        )
        back_button.callback = self.back_to_parent
        self.add_item(back_button)
    
    async def back_to_parent(self, interaction):
        """Go back one layer to either group view or cog view"""
        if self.parent_view == "group" and self.parent_group:
            # If we came from a group view, go back to that group
            view = GroupHelpView(self.help_command, self.parent_group, self.cog, self.mapping)
            view.original_author = self.original_author
            view.invoking_message = self.invoking_message
            
            # Create the group help embed
            embed = discord.Embed(
                title=f"Group: {self.parent_group.name}", 
                description=self.parent_group.description or "All commands related to this group",
                color=discord.Colour.gold(), 
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add base command as #1
            embed.add_field(
                name=f"1  {COMMAND_PREFIX}{self.parent_group.name}",
                value=f"\n{self.parent_group.help or 'No description available.'}",
                inline=False
            )
            
            # Add all subcommands starting from #2
            for idx, subcmd in enumerate(self.parent_group.commands, 2):
                if not subcmd.hidden:
                    embed.add_field(
                        name=f"{idx}  {COMMAND_PREFIX}{self.parent_group.name} {subcmd.name}", 
                        value=subcmd.help or "No description available.", 
                        inline=False
                    )
            
            # Update footer
            embed.set_footer(text=BOTVERSION)
        else:
            # If we came directly from a cog view, go back to the cog
            view = CogHelpView(self.help_command, self.cog, self.mapping)
            view.original_author = self.original_author
            view.invoking_message = self.invoking_message
            
            # Create the cog help embed
            embed = await self.help_command.create_cog_embed(self.cog)
        
        try:
            # Update the message with the parent view
            await interaction.response.edit_message(embed=embed, view=view)
            
            # Make sure to store the message reference properly
            try:
                view.message = interaction.message
            except:
                try:
                    view.message = await interaction.original_response()
                except:
                    pass
        except Exception:
            pass


class ButtonHelpCommand(commands.HelpCommand):
    r"""
    A custom help command class that extends the default help command of discord.py.
    This class provides methods to send help messages containing information about the bot's commands, groups, and modules.
    It uses Discord UI buttons for navigation between different help pages.
    """
    def __init__(self):
        super().__init__()
    
    def get_destination(self):
        """Override to ensure we're always responding in the context"""
        return self.context
    
    async def send_bot_help(self, mapping):
        r'''
        Sends a help message containing all available commands for the bot with buttons for navigation.
        Ensures only the command author can interact with the message.
        
        Parameters:
            mapping (dict): A dictionary containing all the bot's cogs and their associated commands.
            
        Returns:
            None
        '''
        # Create the main help embed
        embed = await self.create_bot_embed(mapping)
        
        # Create the main help view with buttons for navigation
        view = MainHelpView(self, mapping)
        view.original_author = self.context.author  # Set the original command author
        view.invoking_message = self.context.message  # Store the original command message
        
        # Send in the channel
        ctx = self.get_destination()
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    async def send_cog_help(self, cog):
        r'''
        Sends a help message containing all available commands for a specific cog with buttons for navigation.
        Ensures only the command author can interact with the message.
        
        Parameters:
            cog (commands.Cog): The cog to get the commands for.
            
        Returns:
            None
        '''
        # Create the cog help embed
        embed = await self.create_cog_embed(cog)
        
        # Create the cog help view with buttons for navigation
        view = CogHelpView(self, cog, self.get_bot_mapping())
        view.original_author = self.context.author  # Set the original command author
        view.invoking_message = self.context.message  # Store the original command message
        
        # Send in the channel
        ctx = self.get_destination()
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    async def send_command_help(self, cmd):
        r'''
        Sends a help message containing information about a specific command with a back button.
        Ensures only the command author can interact with the message.
        
        Parameters:
            cmd (commands.Command): The command to get help for.
            
        Returns:
            None
        '''
        # Create the command help embed
        embed = await self.create_command_embed(cmd)
        
        # Determine which cog this command belongs to for the back button
        cog = cmd.cog
        
        # Create the command help view with a back button
        view = CommandHelpView(self, cmd, cog, self.get_bot_mapping())
        view.original_author = self.context.author  # Set the original command author
        view.invoking_message = self.context.message  # Store the original command message
        
        # Send in the channel
        ctx = self.get_destination()
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    async def send_group_help(self, group):
        r'''
        Sends a help message containing all available commands for a specific group.
        Ensures only the command author can interact with the message.
        
        Parameters:
            group (commands.Group): The group to get the commands for.
            
        Returns:
            None
        '''
        # For groups, we'll use the same flow as for commands but with additional subcommands info
        embed = discord.Embed(
            title=f"Group: {group.name}", 
            description=group.description or "All commands related to this group",
            color=discord.Colour.gold(), 
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name=f"1  {COMMAND_PREFIX}{group.name}",
            value=f"\n{group.help or 'No description available.'}",
            inline=False
        )
        
        # Add all subcommands
        for index, command in enumerate(group.commands, 2):
            if not command.hidden:
                embed.add_field(
                    name=f"{index}  {COMMAND_PREFIX}{group.name} {command.name}", 
                    value=command.help or "No description available.", 
                    inline=False
                )
        embed.set_footer(text=BOTVERSION)
        # Create the group help view with navigation buttons
        view = GroupHelpView(self, group, group.cog, self.get_bot_mapping())
        view.original_author = self.context.author  # Set the original command author
        view.invoking_message = self.context.message  # Store the original command message
        
        # Send in the channel
        ctx = self.get_destination()
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    async def create_bot_embed(self, mapping, current_page=0, buttons_per_page=24):
        """Create the main help embed with all cogs/modules"""
        embed = discord.Embed(
            title="All Commands", 
            description="Click the numbered buttons below to navigate to specific modules", 
            color=discord.Colour.gold(), 
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add field for each cog with its commands
        index = 1 + current_page * buttons_per_page
        start_idx = current_page * buttons_per_page
        end_idx = start_idx + buttons_per_page
        cogs_list = [cog for cog, commands in mapping.items() if cog and any(not cmd.hidden for cmd in commands)]
        
        for cog in cogs_list[start_idx:end_idx]:
            cog_name = cog.qualified_name
            filtered_commands = await self.filter_commands(mapping[cog], sort=False)
            
            if filtered_commands:
                command_names = [f'{COMMAND_PREFIX}{command.name}' for command in filtered_commands if not command.hidden]
                formatted_command_names = '\n'.join(command_names)
                embed.add_field(name=f"{index}. {cog_name}", value=formatted_command_names, inline=True)
                index += 1
        
        # Add footer with version info
        embed.set_footer(text=BOTVERSION)
        return embed

    async def create_cog_embed(self, cog, current_page=0, buttons_per_page=23):
        """Create an embed for a specific cog/module with numbered commands"""
        embed = discord.Embed(
            title=f"Module: {cog.qualified_name}", 
            description=cog.description or "Click the numbered buttons below to see details for specific commands", 
            color=discord.Colour.gold(), 
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add field for each command with its number
        start_idx = current_page * buttons_per_page
        end_idx = start_idx + buttons_per_page
        command_index = 1 + start_idx
        for command in cog.get_commands()[start_idx:end_idx]:
            if not command.hidden:
                aliases = [alias for alias in command.aliases]
                aliases_text = f"{'No aliases' if len(aliases) == 0 else ('Alias: ' + ', '.join(aliases) if len(aliases) == 1 else 'Aliases: ' + ', '.join(aliases))}"
                embed.add_field(
                    name=f"{command_index}. {command.name}",
                    value=f"{aliases_text}\n{command.help or 'No description available.'}",
                    inline=True
                )
                command_index += 1
        
        # Add footer with version info
        embed.set_footer(text=BOTVERSION)
        return embed

    async def create_command_embed(self, cmd):
        """Create an embed for a specific command"""
        embed = discord.Embed(
            title=f"Command: {cmd.name}", 
            description=cmd.help or "No description available.",
            color=discord.Colour.gold(), 
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add usage information
        if cmd.usage:
            # Check if it's a subcommand (has a parent) and include full command path
            if hasattr(cmd, 'parent') and cmd.parent:
                full_command_name = f"{cmd.parent.name} {cmd.name}"
                embed.add_field(name="Usage", value=f"{COMMAND_PREFIX}{full_command_name} {cmd.usage}", inline=False)
            else:
                embed.add_field(name="Usage", value=f"{COMMAND_PREFIX}{cmd.name} {cmd.usage}", inline=False)
        
        # Add aliases if any
        if cmd.aliases:
            embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
        
        # Add signature/arguments
        if cmd.signature:
            argument_text = "\n< > is a <required> argument.\n[ ] is an [optional] argument."
            clean_signature = re.sub(r'=[^\]]+(?=\])', '', cmd.signature)
            
            # Check if it's a subcommand (has a parent) and include full command path
            if hasattr(cmd, 'parent') and cmd.parent:
                full_command_name = f"{cmd.parent.name} {cmd.name}"
                embed.add_field(
                    name="Usage", 
                    value=f"{COMMAND_PREFIX}{full_command_name} {clean_signature}{argument_text}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Usage", 
                    value=f"{COMMAND_PREFIX}{cmd.name} {clean_signature}{argument_text}",
                    inline=False
                )
        else:
            # Check if it's a subcommand (has a parent) and include full command path
            if hasattr(cmd, 'parent') and cmd.parent:
                full_command_name = f"{cmd.parent.name} {cmd.name}"
                embed.add_field(
                    name="Usage",
                    value=f"{COMMAND_PREFIX}{full_command_name}\nThis command has no extra arguments.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Usage",
                    value=f"{COMMAND_PREFIX}{cmd.name}\nThis command has no extra arguments.",
                    inline=False
                )
        
        # Add footer with version info
        embed.set_footer(text=BOTVERSION)
        return embed

    async def filter_commands(self, commands, *, sort=True, key=None):
        # Override default filter_commands to bypass all checks when generating help content
        # so that the economy permission check doesn't fire when listing economy commands
        commands = [c for c in commands if not c.hidden]
        
        if sort:
            if key:
                commands = sorted(commands, key=key)
            else:
                commands = sorted(commands)
                
        return commands