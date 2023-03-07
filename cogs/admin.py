import os
import git
import discord
import asyncio
from configparser import ConfigParser
from discord.ext import commands

path = os.path.abspath(os.getcwd())
config = ConfigParser()
config.read(rf'{path}/config.ini')
owner_id = int(config['BOTCONFIG']['ownerid'])

MSG_DEL_DELAY = 3

class MemberRoles(commands.MemberConverter):
    async def convert(self, ctx, argument):
        member = await super().convert(ctx, argument)
        return [role.name for role in member.roles[1:]] # Remove everyone role!

class adminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
            print('Admin module online')
    
    @commands.command(aliases=["update"])
    async def update_bot(self, ctx):
        if ctx.author.id == owner_id:
            repo = git.Repo(path)
            repo.remotes.origin.fetch()
            commits_behind = len(list(repo.iter_commits('master..origin/master')))
            commits_ahead = len(list(repo.iter_commits('origin/master..master')))
            bot_msg1 = await ctx.send(f'{commits_behind} commits behind, {commits_ahead} commits ahead')
            
            if commits_behind > 0 and commits_ahead > 0:
                repo.remotes.origin.push()
                repo.remotes.origin.pull()
                bot_msg2 = await ctx.send('KirBot local and remote updated')
            elif commits_behind > 0:
                repo.remotes.origin.pull()
                bot_msg2 = await ctx.send('KirBot local updated')	
            elif commits_ahead > 0:
                repo.remotes.origin.push()
                bot_msg2 = await ctx.send('KirBot remote updated')
            else:
                bot_msg2 = await ctx.send('KirkBot is already up to date with the remote')
        await ctx.message.delete(delay=MSG_DEL_DELAY)
        await bot_msg1.delete(delay=MSG_DEL_DELAY)
        await bot_msg2.delete(delay=MSG_DEL_DELAY)
    
    @commands.command()
    async def roles(self, ctx, *, member: MemberRoles):
        """Tells you a member's roles."""
        await ctx.send('I see the following roles:``` '+', '.join(member)+'```')
    
    @commands.command(aliases=["wh"])
    async def webhook(self, ctx, webhook_name:str, message:str):
        # async def create_webhook():
        #     server_id = ctx.guild.id
        #     channel_id = ctx.channel.id
        #     webhook_avatar_url = self.bot.user.avatar.url
        #     server = self.bot.get_guild(server_id)
        #     channel = server.get_channel(channel_id)
        #     webhook = await channel.create_webhook(name=webhook_name, avatar=webhook_avatar_url)
        #     return webhook
        
        # async def send_webhook_message(content:str):
        #     webhook = await create_webhook()
        #     await webhook.send(content)
        
        # async def my_function(mesage:str):
        #     await send_webhook_message(mesage)
        
        # await my_function(message)
        server_id = ctx.guild.id
        channel_id = ctx.channel.id
        server = self.bot.get_guild(server_id)
        channel = server.get_channel(channel_id)
        # webhook_avatar_url:str = self.bot.user.avatar.url
        webhook_avatar_url = 'https://cdn.discordapp.com/avatars/988870398278004757/712d9a6bb8a33ffe767182c9886a6385.png'
        print (webhook_avatar_url)
        webhook = await channel.create_webhook(name=str(webhook_name), avatar='https://cdn.discordapp.com/avatars/988870398278004757/712d9a6bb8a33ffe767182c9886a6385.png')
        await webhook.send(message)
        print (webhook.url)
    
async def setup(bot):
    await bot.add_cog(adminCommands(bot))

    # @commands.command()
    # @commands.has_permissions(administrator=True)
    # async def warn(self, ctx, member:discord.Member=None, *, reason=None):
    #     '''warns a user'''
    #     try:
    #         first_warning = False
    #         commands.warnings[ctx.guild.id][member.id][0] += 1
    #         commands.warnings[ctx.guild.id][member.id][1].append((ctx.author.id, reason))

    #     except KeyError:
    #         first_warning = True
    #         commands.warnings[ctx.guild.id][member.id] = [1, [(ctx.author.id, reason)]]

    #     count = commands.warnings[ctx.guild.id][member.id][0]

    #     with open(f"{ctx.guild.id}.txt", mode="a") as f:
    #         f.write(f"{member.id} {ctx.author.id} {reason}\n")

    #     await ctx.send(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")



    # @commands.command()
    # @commands.has_permissions(administrator=True)
    # async def member(self, ctx):
    #     '''member options of server'''    #!dont work innit
    #     guildID = ctx.guild.id

    #     guild = self.bot.get_guild(guildID)
    #     memberCount = guild.members.member_count
    #     await ctx.reply(f'```{memberCount}```')
        
        

    # @commands.command()
    # @commands.has_permissions(administrator=True)
    # async def ban(self, ctx, member:discord.Member, *, reason=None):
    #     '''bans a user'''
    #     guild = ctx.guild
    #     author = ctx.message.author
    #     if author.guild_permissions.administrator == False:
    #         embed4=discord.Embed(color=discord.Colour.red(), timestamp=discord.utils.utcnow(), title="Missing Permissions!", description="You don't have the required permissions to use this command!")
    #         message1 = await ctx.send(embed=embed4)    
    #         sleeper=5
    #         await asyncio.sleep(sleeper) 
    #         await message1.delete()
    #         return  
    #     if member.guild_permissions.administrator and member != None:
    #         embed=discord.Embed(color=discord.Colour.red(), title="Administrator", description="This user is an administrator and is not allowed to be banned.")
    #         message2 = await ctx.send(embed=embed)
    #         sleeper=5
    #         await asyncio.sleep(sleeper)
    #         await message2.delete()
    #         return
    #     if reason == None:
    #         embed1=discord.Embed(color=discord.Colour.red(), title="Reason Required!", description="You must enter a reason to ban this member.")    
    #         message3 = ctx.send(embed=embed1)
    #         sleeper=5
    #         await asyncio.sleep(sleeper)
    #         await message3.delete()
    #         return
    #     else:
    #         guild = ctx.guild
    #         await member.ban()
    #         embed2=discord.Embed(color=discord.Colour.green(), timestamp=discord.utils.utcnow(), title="Member Banned", description=f"Banned: {member.mention}\n Moderator: **{author}** \n Reason: **{reason}**")
    #         embed3=discord.Embed(color=discord.Colour.green(), timestamp=discord.utils.utcnow(), title=f"You've been banned from **{guild}**!", description=f"Target: {member.mention}\nModerator: **{author.mention}** \n Reason: **{reason}**")
    #         message4 = await ctx.send(embed=embed2)
    #         message5 = await ctx.send("✔ User has been notified.")
    #         sleeper=5
    #         await asyncio.sleep(sleeper)
    #         await message4.delete()
    #         await message5.delete()
    #         await member.send(embed=embed3)


    # @commands.command(name='perm check', aliases=['perms', 'permissions'])
    # @commands.has_permissions(administrator=True)
    # @commands.guild_only()
    # async def check_permissions(self, ctx, *, member: discord.Member=None):
    #     """A simple command which checks a members Guild Permissions. If member is not provided, the author will be checked."""

    #     if not member:
    #         member = ctx.message.author
    #     # Here we check if the value of each permission is True.
    #     perms = '\n'.join(perm for perm, value in member.guild_permissions if value)
    #     await ctx.send(perms)
    #     for perms in member.guild_permissions:
    #         if getattr(member.guild_permissions, value = True):
    #             '\n'.join(perms)

                    

    #     # And to make it look nice, we wrap it in an Embed
    #     embed = discord.Embed(title='Permissions for:', description=ctx.guild.name, colour=member.colour)
    #     embed.set_author(name=str(member))

    #     await ctx.send(ctx.author)
    #     # \uFEFF is a Zero-Width Space, which basically allows us to have an empty field name.
    #     embed.add_field(name='dot', value=perms)

    #     await ctx.send(content=None, embed=embed)
    #     # Thanks to Gio for the Command.


    # @commands.command(name='embed')
    # @commands.has_permissions(administrator=True)
    # @commands.guild_only()
    # async def embed(self, ctx):
    #     """embed test"""
        
    #     field1 = str(f'{ctx.message.author} shit')
    #     valuefield1 = str(f'{ctx.guild.name} piss')

    #     embedVar = discord.Embed(color=discord.Colour.red())
    #     embedVar.add_field(name=field1, value=valuefield1, inline=False)
    #     embedVar.add_field(name="Field2", value="hi2", inline=False)
    #     # await message.channel.send(embed=embedVar)
    #     await ctx.send(embed=embedVar)




    # @commands.command()
    # @commands.command()
    # @commands.command()
    # @commands.command()
    # @commands.command()
    # @commands.command()






    
    
    
# _permissions_dict = dict(iter(member.guild_permissions))
# permissions = (
#   ", ".join(
#     [
#       # e.g. (`manage_members` -> `Manage Members`)
#       (permission.replace("_", " ").title())
#       for permission in _permissions_dict
#       if _permissions_dict[permission]
#     ]
#   )
#   if not _permissions_dict["administrator"]
#   else "Administrator"
# )