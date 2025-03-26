import aiosqlite
import discord

from discord.ext import commands
from datetime import datetime, timezone
from cogs.utils.constants import AUTOROLE_DATABASE, BOTVERSION

class Autorole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Autorole module online')
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with aiosqlite.connect(AUTOROLE_DATABASE) as con:
            async with con.execute('SELECT join_role_ids FROM autorole_data WHERE server_id = ?', (member.guild.id,)) as cursor:
                role_data = await cursor.fetchone()
            if role_data and role_data[0]:
                role_ids = [int(role_id) for role_id in role_data[0].split(',')]
                roles = [member.guild.get_role(role_id) for role_id in role_ids]
                roles = [role for role in roles if role]
                if roles:
                    await member.add_roles(*roles, reason="Autorole")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ...
    
    @commands.group(name='joinrole', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joinrole_base(self, ctx):
        async with aiosqlite.connect(AUTOROLE_DATABASE) as con:
            async with con.execute('SELECT join_role_ids FROM autorole_data WHERE server_id = ?', (ctx.guild.id,)) as cursor:
                role_data = await cursor.fetchone()
            if role_data and role_data[0]:
                role_ids = [int(role_id) for role_id in role_data[0].split(',')]
                roles = [ctx.guild.get_role(role_id) for role_id in role_ids]
                roles = [role for role in roles if role]
                if roles:
                    role_mentions = ', '.join(role.mention for role in roles)
                    embed = discord.Embed(title='Joinrole', description=f'Current join roles status for {ctx.guild.name}:\n\nCurrent roles applied to members on join are: {role_mentions}', color=0x00ff00, timestamp=datetime.now(timezone.utc))
                else:
                    embed = discord.Embed(title='Joinrole', description=f'Current join role status for {ctx.guild.name}:\n\nThis server does not have any autoroles set.', color=0xff0000, timestamp=datetime.now(timezone.utc))
            else:
                embed = discord.Embed(title='Joinrole', description=f'Current join role status for {ctx.guild.name}:\n\nThis server does not have any autoroles set.', color=0xff0000, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=BOTVERSION)
        await ctx.reply(embed=embed)
    
    @joinrole_base.command(name='add')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joinrole_add(self, ctx, *roles: discord.Role):
        async with aiosqlite.connect(AUTOROLE_DATABASE) as con:
            async with con.execute('SELECT join_role_ids FROM autorole_data WHERE server_id = ?', (ctx.guild.id,)) as cursor:
                role_data = await cursor.fetchone()
            if role_data and role_data[0]:
                role_ids = [int(role_id) for role_id in role_data[0].split(',')]
                role_ids.extend([role.id for role in roles])
                await con.execute('UPDATE autorole_data SET join_role_ids = ? WHERE server_id = ?', (','.join(str(role_id) for role_id in role_ids), ctx.guild.id))
            else:
                await con.execute('INSERT INTO autorole_data (server_id, join_role_ids) VALUES (?, ?)', (ctx.guild.id, ','.join(str(role.id) for role in roles)))
            await con.commit()
            role_mentions = ', '.join(role.mention for role in roles)
            await ctx.reply(f'Join roles set to: {role_mentions}')
    
    @joinrole_base.command(name='remove')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joinrole_remove(self, ctx, *roles: discord.Role):
        async with aiosqlite.connect(AUTOROLE_DATABASE) as con:
            async with con.execute('SELECT join_role_ids FROM autorole_data WHERE server_id = ?', (ctx.guild.id,)) as cursor:
                role_data = await cursor.fetchone()
            if role_data and role_data[0]:
                role_ids = [int(role_id) for role_id in role_data[0].split(',')]
                role_ids = [role_id for role_id in role_ids if role_id not in [role.id for role in roles]]
                if role_ids:
                    await con.execute('UPDATE autorole_data SET join_role_ids = ? WHERE server_id = ?', (','.join(str(role_id) for role_id in role_ids), ctx.guild.id))
                else:
                    await con.execute('DELETE FROM autorole_data WHERE server_id = ?', (ctx.guild.id,))
                await con.commit()
                role_mentions = ', '.join(role.mention for role in roles)
                await ctx.reply(f'Join roles removed: {role_mentions}')
            else:
                await ctx.reply('This server does not have any autoroles set.')

async def setup(bot):
    await bot.add_cog(Autorole(bot))