from random import random
import discord
from discord.ext import commands, tasks


class MessageRepeater(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._tasks = []

    @commands.Cog.listener()
    async def on_ready(self):
        print('Message repeater module online')
    
    async def before_repeater_stream(self):
        print('Waiting to start get_tweet_stream')
        await self.bot.wait_until_ready()
        print('get_tweet_stream started')
    
    async def after_repeater_stream(self):
        print('Repeater stream stopped')
    
    def task_launcher(self, ctx, input: str = None, interval: int = None):
        new_task = tasks.loop(interval=interval)
        new_task.before_loop(self.before_repeater_stream())
        new_task.after_loop(self.after_repeater_stream())
        new_task.start(ctx=ctx, input=input)
        self._tasks.append(new_task)
    
    #@commands.has_permissions(administrator=True)
    @commands.group(name='repeater', aliases=['rp'], invoke_without_command=True)
    async def repeater_base(self, ctx):
        await ctx.send('refer to help command for more info')

    @repeater_base.command(name='currentstream', aliases=['cs'], invoke_without_command=True)
    async def repeater_currentstream(self, ctx):
        if self.get_tweet_stream.is_running():
            current = self.get_tweet_stream.get_task()
            await ctx.send(f'current stream is: {current}')
        else:
            await ctx.send('no stream is running')

    @commands.has_permissions(administrator=True)
    @repeater_base.command(name='startstream', aliases=['ss'], invoke_without_command=True)
    async def repeater_command(self, ctx, interval: int = 10, *, input: str = None):
        self.task_launcher(ctx=ctx, input=input, interval=interval)
        self.get_tweet_stream.change_interval(minutes=interval)
        #pass

    @commands.has_permissions(administrator=True)
    @repeater_base.command(name='stopstream', aliases=['st'], invoke_without_command=True)
    async def stop_stream(self, ctx):
        self.get_tweet_stream.stop()
        await ctx.send('stream stopped')
        #pass
    
    
    @commands.has_permissions(administrator=True)
    @commands.command()
    async def start_task(self, ctx, *args):
        """Command that launches a new task with the arguments given"""
        self.task_launcher(*args, seconds=1)
        await ctx.send('Task started!')



def setup(bot):
    bot.add_cog(MessageRepeater(bot))
