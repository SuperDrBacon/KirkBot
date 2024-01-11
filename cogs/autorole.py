import discord
import os
import aiosqlite as sql
import cogs.utils.functions as functions
from configparser import ConfigParser
from discord.ext import commands
from discord.ui import Button, View

ospath = os.path.abspath(os.getcwd())

autorole_database = rf'{ospath}/cogs/autorole_data.db'
info, config = ConfigParser(), ConfigParser()
info.read(rf'{ospath}/info.ini')

botversion = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']


class Autorole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        functions.checkForFile(os.path.dirname(autorole_database), os.path.basename(autorole_database), True, 'autorole')
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Autorole module online')
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        ...
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with sql.connect(autorole_database) as con:
            async with con.execute('SELECT server_id, user_id, join_role, base_role, roles FROM autorole_data WHERE server_id = ? AND user_id = ?', (member.guild.id, member.id)) as cursor:
                role_data = await cursor.fetchone()
            _, _, join_role, base_role, roles = role_data
            
            if base_role is not None:
                if base_role in member.guild.roles:
                    await member.add_roles(base_role)
                if roles is not None:
                    for role in roles:
                        if role in member.guild.roles:
                            await member.add_roles(role)
            
            else:
                if join_role in member.guild.roles:
                    await member.add_roles(join_role)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ...
    
    @commands.group(name='autorole', aliases=['ar'], description='All commands related to autorole', invoke_without_command=True)
    # @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def autorole_base(self, ctx):
        # view = AutoroleButtons()
        # await ctx.send('All commands related to autorole', view=view)
        button = Button(style=discord.ButtonStyle.green, label='Add')
        view = View()
        view.add_item(button)
        await ctx.send('All commands related to autorole', view=view)
        ...
    
    @autorole_base.command(name='add', aliases=['a'], description='Add a role to the autorole list')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def autorole_add(self, ctx, role: discord.Role):
        # async with sql.connect(autorole_database) as con:
            # async with con.execute('SELECT ', (,)) as cursor:
                
        ...

async def setup(bot):
    await bot.add_cog(Autorole(bot))

class AutoroleButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
    
    @discord.ui.button(label='Add', style=discord.ButtonStyle.green)
    async def add(self, button: discord.ui.Button, interaction: discord.Interaction):
        # button.style = discord.ButtonStyle.red
        # button.disabled = True
        await interaction.response.edit_message(content='Add a role to the autorole list', ephemeral=True)
        # await interaction.respond.defer()
    # ...