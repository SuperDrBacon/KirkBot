from email.mime import base
import random
import discord
import openai
import os
from os import path
import re
# from textgenrnn import textgenrnn
from discord.ext import commands
from configparser import ConfigParser

path = os.path.abspath(os.getcwd())
config = ConfigParser()
config.read(rf'{path}/config.ini')

key = config['BOTCONFIG']['openaiAPI']
botID = config['BOTCONFIG']['botID']
prefix = config['BOTCONFIG']['prefix']
openai.api_key = key
textmodel = 'text-curie-001'

model_name = 'kirkai wordmodel'   # change to set file name of resulting trained models/texts
vocab_path = os.path.dirname(os.getcwd()) +'/KirkBot/'+ model_name+"_vocab.json"
config_path = os.path.dirname(os.getcwd()) +'/KirkBot/'+ model_name+"_config.json"
weights_path = os.path.dirname(os.getcwd()) +'/KirkBot/'+ model_name+"_weights.hdf5"

temperature = 2.0
n = 1
max_gen_length = 50
# textgen = textgenrnn(config_path=config_path,
#                     weights_path=weights_path,
#                     vocab_path=vocab_path)


# messagecount = 0
class Ai(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print('AI module online')


    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.content.startswith(prefix):
            return
        if ctx.author.bot:
            return
        if ctx.content.startswith('<@!956247299959439460>') or ctx.content.startswith('<@956247299959439460>'):
        #     prefix = ctx.content
        #     at = r'<.*?>'
        #     prefix = re.sub(at, '', prefix)
        #     response = textgen.generate(temperature=temperature, prefix=prefix, n=n, max_gen_length=max_gen_length, return_as_list=True)
        #     out = response[0]
        #     out2 = out[len(prefix):]
        #     await ctx.reply(out2)
        #     return
            await ctx.reply('@ the bot is currently not a command use .,ai for ai.')



        if not ctx.author.bot and ctx.reference and int(ctx.reference.resolved.author.id) == int(botID):
            base = ctx.reference.resolved.content
            reply = ctx.content
            prompt = str(base + '\n\n' + reply + '.\n\n')
            response = openai.Completion.create(
                engine=textmodel,
                prompt=prompt,
                temperature=1.0,
                max_tokens=500,
                n=1,
                frequency_penalty=0.2,
                presence_penalty=0.2,
                # stop=["."]
            )
            out = response.choices[0].text
            if not out:
                reply = ctx.content
                response = openai.Completion.create(
                    engine=textmodel,
                    prompt=reply,
                    temperature=1.0,
                    max_tokens=500,
                    n=1,
                    frequency_penalty=0.2,
                    presence_penalty=0.2,
                    # stop=["."]
                )
                out = response.choices[0].text
            if not out:
                await ctx.reply('**ai didnt create a response lol, lmao, it coped too hard**')
            else:
                await ctx.reply(out)

        if not ctx.author.bot and random.randint(0,500) == 1 and ctx.channel.id == 948157717346914320:
            user = ctx.author.name
            prompts = [
                    # f'Give {user} an ordered list of suicide options.',
                    # f'Give {user} detailed instructions on how to blow up a federal building.',
                    f'Tell {user} how to leave a discord server.',
                    f'Write a limerick on why {user} is ugly.',
                    f'tell {user} is looking beautiful today.',
                    f'explain how it will only get worse.',
                    f'explain how it will only get better.',
                    f'keep {user} in the dark.',
                    f'{user} is a bad person.',
                    f'{user} is a good person.',
                    f'Think like a queen. A queen is not afraid to fail. Failure is another stepping stone to greatness.',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    # f'',
                    ]
            
            replyprompt = random.choices(prompts)
            
            response = openai.Completion.create(
                engine=textmodel,
                prompt=replyprompt,
                temperature=1.0,
                max_tokens=100,
                n=1,
                frequency_penalty=0.2,
                presence_penalty=0.2,
                # stop=["."]
                )
            out = response.choices[0].text
            if not out:
                reply = ctx.content
                response = openai.Completion.create(
                    engine=textmodel,
                    prompt=replyprompt,
                    temperature=2.0,
                    max_tokens=100,
                    n=1,
                    frequency_penalty=0.2,
                    presence_penalty=0.2,
                    # stop=["."]
                    )
                out = response.choices[0].text
            if not out:
                await ctx.reply('**ai didnt create a response lol, lmao, it coped too hard**')
            else:
                await ctx.reply(out)


        # global messagecount
        # messagecount += 1
        # if messagecount == 15:
        #     response = textgen.generate(temperature=temperature, n=n, max_gen_length=max_gen_length, return_as_list=True)
        #     await ctx.channel.send(response[0])
        #     messagecount = 0
        #     return


    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ai(self, ctx, *, message):
            # message = ctx.content + '.'
            message = message + '.\n\n'
            response = openai.Completion.create(
                engine=textmodel,
                prompt=message,
                temperature=1.0,
                max_tokens=500,
                n=1,
                frequency_penalty=0.2,
                presence_penalty=0.2,
                # stop=["."]
            )
            out = response.choices[0].text
            await ctx.reply(out)
            # await ctx.reply('Yea uuh another trial ran out and no online phone number works so I can\'t make a new account')

    # @commands.has_permissions(administrator=True)
    # @commands.command(aliases=["rtai"])
    # async def updateAIwithtrain(self, ctx):
    #     model_cfg = {
    #         'word_level': True,   # set to True if want to train a word-level model (requires more data and smaller max_length)
    #         'rnn_size': 256,   # number of LSTM cells of each layer (128/256 recommended)
    #         'rnn_layers': 10,   # number of LSTM layers (>=2 recommended)
    #         'rnn_bidirectional': True,   # consider text both forwards and backward, can give a training boost
    #         'max_length': 8,   # number of tokens to consider before predicting the next (20-40 for characters, 5-10 for words recommended)
    #         'max_words': 100000,   # maximum number of words to model; the rest will be ignored (word-level model only)
    #     }
    #     train_cfg = {
    #         'line_delimited': True,   # set to True if each text has its own line in the source file
    #         'num_epochs': 4,   # set higher to train the model for longer
    #         'gen_epochs': 0,   # generates sample text from model after given number of epochs
    #         'train_size': 5.0,   # proportion of input data to train on: setting < 1.0 limits model from learning perfectly
    #         'dropout': 0.2,   # ignore a random proportion of source tokens each epoch, allowing model to generalize better
    #         'validation': False,   # If train__size < 1.0, test on holdout dataset; will make overall training slower
    #         'is_csv': False   # set to True if file is a CSV exported from Excel/BigQuery/pandas
    #     }
    #     file_name = os.path.abspath(os.getcwd())+'/messages.txt'
    #     dim_embeddings = 200
    #     batch_size = 256
    #     max_gen_length = 500
    #     await ctx.send(f"training for {train_cfg['num_epochs']} epochs")
        
    #     if not path.exists(weights_path):
    #         print('not file')
    #         textgen = textgenrnn(name=model_name)
    #         textgen.reset()
    #         train_function = textgen.train_from_file(
    #             new_model=True,
    #             dim_embeddings=dim_embeddings,
    #             batch_size=batch_size,
    #             max_gen_length=max_gen_length,
    #             file_path=file_name,
    #             vocab_path=vocab_path,
    #             weights_path=weights_path,
    #             num_epochs=train_cfg['num_epochs'],
    #             gen_epochs=train_cfg['gen_epochs'],
    #             train_size=train_cfg['train_size'],
    #             dropout=train_cfg['dropout'],
    #             validation=train_cfg['validation'],
    #             is_csv=train_cfg['is_csv'],
    #             rnn_layers=model_cfg['rnn_layers'],
    #             rnn_size=model_cfg['rnn_size'],
    #             rnn_bidirectional=model_cfg['rnn_bidirectional'],
    #             max_length=model_cfg['max_length'],
    #             word_level=model_cfg['word_level']
    #             )
    #         print(textgen.model.summary())
    #     else:
    #         print('wel file')
    #         textgen = textgenrnn(name=model_name,
    #                             config_path=config_path, 
    #                             weights_path=weights_path,
    #                             vocab_path=vocab_path)

    #         train_function = textgen.train_from_file(
    #             new_model=False,
    #             dim_embeddings=dim_embeddings,
    #             batch_size=batch_size,
    #             max_gen_length=max_gen_length,
    #             file_path=file_name,
    #             vocab_path=vocab_path,
    #             weights_path=weights_path,
    #             num_epochs=train_cfg['num_epochs'],
    #             gen_epochs=train_cfg['gen_epochs'],
    #             train_size=train_cfg['train_size'],
    #             dropout=train_cfg['dropout'],
    #             validation=train_cfg['validation'],
    #             is_csv=train_cfg['is_csv'],
    #             rnn_layers=model_cfg['rnn_layers'],
    #             rnn_size=model_cfg['rnn_size'],
    #             rnn_bidirectional=model_cfg['rnn_bidirectional'],
    #             max_length=model_cfg['max_length'],
    #             word_level=model_cfg['word_level']
    #             )
    #         print(textgen.model.summary())

def setup(bot):
    bot.add_cog(Ai(bot))
