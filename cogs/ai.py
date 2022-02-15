import discord
import openai
import os
import re
from textgenrnn import textgenrnn
from discord.ext import commands
from configparser import ConfigParser

config = ConfigParser()
configpath = os.path.abspath(os.getcwd())
configini = '/'.join([configpath, "config.ini"])
config.read(configini)

key = config['BOTCONFIG']['openaiAPI']
openai.api_key = key

model_name = 'kirkai wordmodel'   # change to set file name of resulting trained models/texts
vocab_path = "C:\py saves\other/"+model_name+"_vocab.json"
config_path = "C:\py saves\other/"+model_name+"_config.json"
weights_path = "C:\py saves\other/"+model_name+"_weights.hdf5"
temperature = 2.5
n = 1
max_gen_length = 15
textgen = textgenrnn(config_path=config_path, 
                    weights_path=weights_path,
                    vocab_path=vocab_path)


messagecount = 0
class Ai(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('logger module online')
    

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot:
            return
        # pass
        if ctx.content.startswith('<@!937050268007268452>') or ctx.content.startswith('<@937050268007268452>'):
            prefix = ctx.content
            at = r'<.*?>'
            prefix = re.sub(at, '', prefix)
            response = textgen.generate(temperature=temperature, prefix=prefix, n=n, max_gen_length=max_gen_length, return_as_list=True)
            await ctx.reply(response[0])
            # print(response)
            return
        global messagecount
        # messagecount += 1
        print(messagecount)
        if messagecount == 15:
            response = textgen.generate(temperature=temperature, n=n, max_gen_length=max_gen_length, return_as_list=True)
            await ctx.channel.send(response[0])
            messagecount = 0
            return


    @commands.command()
    async def ai(self, ctx, *, message):
            # message = ctx.content + '.'
            response = openai.Completion.create(
                engine="text-davinci-001",
                prompt=message,
                temperature=0.9,
                max_tokens=500,
                n=1,
                frequency_penalty=0.2,
                presence_penalty=0.2,
                stop=["."]
            )
            out = response.choices[0].text
            await ctx.reply(out)

def setup(bot):
    bot.add_cog(Ai(bot))
