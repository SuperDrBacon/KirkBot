import discord
import openai
import os
from os import path
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
vocab_path = os.path.abspath(os.getcwd())+'//'+model_name+"_vocab.json"
config_path = os.path.abspath(os.getcwd())+'//'+model_name+"_config.json"
weights_path = os.path.abspath(os.getcwd())+'//'+model_name+"_weights.hdf5"

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
        print('AI module online')


    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot:
            return
        if ctx.content.startswith('<@!937050268007268452>') or ctx.content.startswith('<@937050268007268452>'):
            prefix = ctx.content
            at = r'<.*?>'
            prefix = re.sub(at, '', prefix)
            response = textgen.generate(temperature=temperature, prefix=prefix, n=n, max_gen_length=max_gen_length, return_as_list=True)
            out = response[0]
            out2 = out[len(prefix):]
            await ctx.reply(out2)
            return
        global messagecount
        # messagecount += 1
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
                temperature=1.0,
                max_tokens=500,
                n=1,
                frequency_penalty=0.2,
                presence_penalty=0.2,
                # stop=["."]
            )
            out = response.choices[0].text
            await ctx.reply(out)

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=["rtai"])
    async def updateAIwithtrain(self, ctx):
        model_cfg = {
            'word_level': True,   # set to True if want to train a word-level model (requires more data and smaller max_length)
            'rnn_size': 256,   # number of LSTM cells of each layer (128/256 recommended)
            'rnn_layers': 10,   # number of LSTM layers (>=2 recommended)
            'rnn_bidirectional': True,   # consider text both forwards and backward, can give a training boost
            'max_length': 10,   # number of tokens to consider before predicting the next (20-40 for characters, 5-10 for words recommended)
            'max_words': 10000,   # maximum number of words to model; the rest will be ignored (word-level model only)
        }
        train_cfg = {
            'line_delimited': True,   # set to True if each text has its own line in the source file
            'num_epochs': 1,   # set higher to train the model for longer
            'gen_epochs': 0,   # generates sample text from model after given number of epochs
            'train_size': 10.0,   # proportion of input data to train on: setting < 1.0 limits model from learning perfectly
            'dropout': 0.2,   # ignore a random proportion of source tokens each epoch, allowing model to generalize better
            'validation': False,   # If train__size < 1.0, test on holdout dataset; will make overall training slower
            'is_csv': False   # set to True if file is a CSV exported from Excel/BigQuery/pandas
        }
        file_name = os.path.abspath(os.getcwd())+'//messages.txt'
        dim_embeddings = 200
        batch_size = 800
        max_gen_length = 50
        await ctx.send(f"training for {train_cfg['num_epochs']} epochs")
        
        if not path.exists(weights_path):
            print('not file')
            textgen = textgenrnn(name=model_name)
            textgen.reset()
            train_function = textgen.train_from_file(
                new_model=True,
                dim_embeddings=dim_embeddings,
                batch_size=batch_size,
                max_gen_length=max_gen_length,
                file_path=file_name,
                vocab_path=vocab_path,
                weights_path=weights_path,
                num_epochs=train_cfg['num_epochs'],
                gen_epochs=train_cfg['gen_epochs'],
                train_size=train_cfg['train_size'],
                dropout=train_cfg['dropout'],
                validation=train_cfg['validation'],
                is_csv=train_cfg['is_csv'],
                rnn_layers=model_cfg['rnn_layers'],
                rnn_size=model_cfg['rnn_size'],
                rnn_bidirectional=model_cfg['rnn_bidirectional'],
                max_length=model_cfg['max_length'],
                word_level=model_cfg['word_level']
                )
            print(textgen.model.summary())
        else:
            print('wel file')
            textgen = textgenrnn(name=model_name,
                                config_path=config_path, 
                                weights_path=weights_path,
                                vocab_path=vocab_path)

            train_function = textgen.train_from_file(
                new_model=False,
                dim_embeddings=dim_embeddings,
                batch_size=batch_size,
                max_gen_length=max_gen_length,
                file_path=file_name,
                vocab_path=vocab_path,
                weights_path=weights_path,
                num_epochs=train_cfg['num_epochs'],
                gen_epochs=train_cfg['gen_epochs'],
                train_size=train_cfg['train_size'],
                dropout=train_cfg['dropout'],
                validation=train_cfg['validation'],
                is_csv=train_cfg['is_csv'],
                rnn_layers=model_cfg['rnn_layers'],
                rnn_size=model_cfg['rnn_size'],
                rnn_bidirectional=model_cfg['rnn_bidirectional'],
                max_length=model_cfg['max_length'],
                word_level=model_cfg['word_level']
                )
            print(textgen.model.summary())

def setup(bot):
    bot.add_cog(Ai(bot))
