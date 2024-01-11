import asyncio
import discord
import os
import sqlite3
import random
import cogs.utils.functions as functions
import datetime as dt
from io import BytesIO
from configparser import ConfigParser
from discord.ext import commands
from typing import Union
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

ospath = os.path.abspath(os.getcwd())
cardspath = rf'{ospath}/playingcards/'
economy_data = rf'{ospath}/cogs/economy_data.db'
info, config = ConfigParser(), ConfigParser()
info.read(rf'{ospath}/info.ini')
config.read(rf'{ospath}/config.ini')
currency_singular = info['ECONOMY']['currency_singular']
currency_plural = info['ECONOMY']['currency_plural']
owner_id = int(config['BOTCONFIG']['ownerid'])
botversion = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']

MSG_DEL_DELAY = 10
STARTING_BALANCE = 1000
STARTING_BANK = 0
ONE_DAY = 86400
SLOTS_ROTATE_DELAY = 0.4
SLOT_SYMBOLS = {
    "🍒": 2,
    "🍊": 3,
    "🍋": 4,
    "🍉": 5,
    "🍇": 6,
    "🍎": 7,
    "🍓": 8,
    "🍍": 10,
    "💰": 20}

CARDS = {
    'clubs_2':          ('Clubs',     'black',  '♣',    '2',        f'{cardspath}clubs_2.png'),
    'clubs_3':          ('Clubs',     'black',  '♣',    '3',        f'{cardspath}clubs_3.png'),
    'clubs_4':          ('Clubs',     'black',  '♣',    '4',        f'{cardspath}clubs_4.png'),
    'clubs_5':          ('Clubs',     'black',  '♣',    '5',        f'{cardspath}clubs_5.png'),
    'clubs_6':          ('Clubs',     'black',  '♣',    '6',        f'{cardspath}clubs_6.png'),
    'clubs_7':          ('Clubs',     'black',  '♣',    '7',        f'{cardspath}clubs_7.png'),
    'clubs_8':          ('Clubs',     'black',  '♣',    '8',        f'{cardspath}clubs_8.png'),
    'clubs_9':          ('Clubs',     'black',  '♣',    '9',        f'{cardspath}clubs_9.png'),
    'clubs_10':         ('Clubs',     'black',  '♣',    '10',       f'{cardspath}clubs_10.png'),
    'clubs_jack':       ('Clubs',     'black',  '♣',    'Jack',     f'{cardspath}clubs_jack.png'),
    'clubs_queen':      ('Clubs',     'black',  '♣',    'Queen',    f'{cardspath}clubs_queen.png'),
    'clubs_king':       ('Clubs',     'black',  '♣',    'King',     f'{cardspath}clubs_king.png'),
    'clubs_ace':        ('Clubs',     'black',  '♣',    'Ace',      f'{cardspath}clubs_ace.png'),
    'diamonds_2':       ('Diamonds',  'red',    '♦',    '2',        f'{cardspath}diamonds_2.png'),
    'diamonds_3':       ('Diamonds',  'red',    '♦',    '3',        f'{cardspath}diamonds_3.png'),
    'diamonds_4':       ('Diamonds',  'red',    '♦',    '4',        f'{cardspath}diamonds_4.png'),
    'diamonds_5':       ('Diamonds',  'red',    '♦',    '5',        f'{cardspath}diamonds_5.png'),
    'diamonds_6':       ('Diamonds',  'red',    '♦',    '6',        f'{cardspath}diamonds_6.png'),
    'diamonds_7':       ('Diamonds',  'red',    '♦',    '7',        f'{cardspath}diamonds_7.png'),
    'diamonds_8':       ('Diamonds',  'red',    '♦',    '8',        f'{cardspath}diamonds_8.png'),
    'diamonds_9':       ('Diamonds',  'red',    '♦',    '9',        f'{cardspath}diamonds_9.png'),
    'diamonds_10':      ('Diamonds',  'red',    '♦',    '10'        f'{cardspath}diamonds_10.png'),
    'diamonds_jack':    ('Diamonds',  'red',    '♦',    'Jack',     f'{cardspath}diamonds_jack.png'),
    'diamonds_queen':   ('Diamonds',  'red',    '♦',    'Queen',    f'{cardspath}diamonds_queen.png'),
    'diamonds_king':    ('Diamonds',  'red',    '♦',    'King',     f'{cardspath}diamonds_king.png'),
    'diamonds_ace':     ('Diamonds',  'red',    '♦',    'Ace',      f'{cardspath}diamonds_ace.png'),
    'hearts_2':         ('Hearts',    'red',    '♥',    '2',        f'{cardspath}hearts_2.png'),
    'hearts_3':         ('Hearts',    'red',    '♥',    '3',        f'{cardspath}hearts_3.png'),
    'hearts_4':         ('Hearts',    'red',    '♥',    '4',        f'{cardspath}hearts_4.png'),
    'hearts_5':         ('Hearts',    'red',    '♥',    '5',        f'{cardspath}hearts_5.png'),
    'hearts_6':         ('Hearts',    'red',    '♥',    '6',        f'{cardspath}hearts_6.png'),
    'hearts_7':         ('Hearts',    'red',    '♥',    '7',        f'{cardspath}hearts_7.png'),
    'hearts_8':         ('Hearts',    'red',    '♥',    '8',        f'{cardspath}hearts_8.png'),
    'hearts_9':         ('Hearts',    'red',    '♥',    '9',        f'{cardspath}hearts_9.png'),
    'hearts_10':        ('Hearts',    'red',    '♥',    '10',       f'{cardspath}hearts_10.png'),
    'hearts_jack':      ('Hearts',    'red',    '♥',    'Jack',     f'{cardspath}hearts_jack.png'),
    'hearts_queen':     ('Hearts',    'red',    '♥',    'Queen',    f'{cardspath}hearts_queen.png'),
    'hearts_king':      ('Hearts',    'red',    '♥',    'King',     f'{cardspath}hearts_king.png'),
    'hearts_ace':       ('Hearts',    'red',    '♥',    'Ace',      f'{cardspath}hearts_ace.png'),
    'spades_2':         ('Spades',    'black',  '♠',    '2',        f'{cardspath}spades_2.png'),
    'spades_3':         ('Spades',    'black',  '♠',    '3',        f'{cardspath}spades_3.png'),
    'spades_4':         ('Spades',    'black',  '♠',    '4',        f'{cardspath}spades_4.png'),
    'spades_5':         ('Spades',    'black',  '♠',    '5',        f'{cardspath}spades_5.png'),
    'spades_6':         ('Spades',    'black',  '♠',    '6',        f'{cardspath}spades_6.png'),
    'spades_7':         ('Spades',    'black',  '♠',    '7',        f'{cardspath}spades_7.png'),
    'spades_8':         ('Spades',    'black',  '♠',    '8',        f'{cardspath}spades_8.png'),
    'spades_9':         ('Spades',    'black',  '♠',    '9',        f'{cardspath}spades_9.png'),
    'spades_10':        ('Spades',    'black',  '♠',    '10',       f'{cardspath}spades_10.png'),
    'spades_jack':      ('Spades',    'black',  '♠',    'Jack',     f'{cardspath}spades_jack.png'),
    'spades_queen':     ('Spades',    'black',  '♠',    'Queen',    f'{cardspath}spades_queen.png'),
    'spades_king':      ('Spades',    'black',  '♠',    'King',     f'{cardspath}spades_king.png'),
    'spades_ace':       ('Spades',    'black',  '♠',    'Ace',      f'{cardspath}spades_ace.png'),
    'card_back':        ('Card',      'void',   '■',    'Back',     f'{cardspath}card_back.png'),
    'joker_black':      ('Joker',     'black',  '🤡',   'Black',    f'{cardspath}joker_black.png'),
    'joker_red':        ('Joker',     'red',    '🤡',   'Red',      f'{cardspath}joker_red.png')}


class Economy(commands.Cog):
    '''
    This module provides commands and functionality related to the economy system of the bot.
    '''
    def __init__(self, bot):
        self.bot = bot
        functions.checkForFile(os.path.dirname(economy_data), os.path.basename(economy_data), True, 'economy')
    
    def check_user(self, user_id:int, user_name:str, server_id:int, unix_time:int):
        '''
        Checks if the user exists in the database and adds them if they don't.

        Args:
            user_id (int): The ID of the user.
            user_name (str): The name of the user.
            server_id (int): The ID of the server.
            unix_time (int): The current Unix time.
        '''
        con = sqlite3.connect(economy_data)
        cur = con.cursor()
        
        cur.execute("SELECT user_id FROM economy_data WHERE user_id = ?", (user_id,))
        result = cur.fetchone()
        
        cur.close()
        con.close()
        if not result:
            self.add_user(user_id, user_name, server_id, unix_time)
    
    def add_user(self, user_id:int, user_name:str, server_id:int, unix_time:int):
        '''
        Adds a new user to the database.

        Args:
            user_id (int): The ID of the user.
            user_name (str): The name of the user.
            server_id (int): The ID of the server.
            unix_time (int): The current Unix time.
        '''
        con = sqlite3.connect(economy_data)
        cur = con.cursor()
        
        data_to_insert = '''INSERT INTO economy_data(
                    USER_ID,
                    USERNAME,
                    SERVER_ID,
                    UNIX_TIME,
                    BALANCE,
                    BANK,
                    SLOTS_WINS,
                    SLOTS_LOSSES,
                    BJ_WINS,
                    BJ_LOSSES,
                    BJ_TIES,
                    CF_WINS,
                    CF_LOSSES
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        data_tuple = (
                    user_id, 
                    user_name, 
                    server_id, 
                    unix_time, 
                    STARTING_BALANCE, 
                    STARTING_BANK,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                    )
        cur.execute(data_to_insert, data_tuple)
        con.commit()
        cur.close()
        con.close()
    
    def get_user_balance(self, user_id:int):
        '''
        Retrieves the balance of a user from the database.
        
        Args:
            user_id (int): The ID of the user.
            server_id (int): The ID of the server.
        
        Returns:
            int: The balance of the user.
        '''
        con = sqlite3.connect(economy_data)
        cur = con.cursor()
        
        cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (user_id,))
        result = cur.fetchone()
        balance = result[0] if result else 0
        
        cur.close()
        con.close()
        return balance
    
    def blackjack_calculate_sum(self, cards):
        '''
        Calculates the sum of a list of blackjack cards.
        
        Args:
            cards (list): A list of blackjack cards.
        
        Returns:
            int: The sum of the values of the cards in the list.
        '''
        sum = 0
        num_aces = 0
        for card in cards:
            rank = card[:-1]
            if rank.isdigit():
                sum += int(rank)
            elif rank in ['J', 'Q', 'K']:
                sum += 10
            elif rank == 'A':
                num_aces += 1
                sum += 11
        while sum > 21 and num_aces > 0:
            sum -= 10
            num_aces -= 1
        return sum
    
    def blackjack_dealer_turn(self, deck, dealer_cards):
        """
        Simulates the dealer's turn in a game of blackjack.
        
        Args:
            deck (list): A list of blackjack cards.
            dealer_cards (list): A list of the dealer's cards.
        
        Returns:
            int: The sum of the dealer's cards.
        """
        dealer_sum = self.blackjack_calculate_sum(dealer_cards)
        while dealer_sum < 17:
            dealer_cards.append(deck.pop())
            dealer_sum = self.blackjack_calculate_sum(dealer_cards)
        return dealer_sum
    
    def blackjack_determine_winner(self, player_sum, dealer_sum):
        """
        Determines the winner of a game of blackjack.

        Args:
            player_sum (int): The sum of the player's cards.
            dealer_sum (int): The sum of the dealer's cards.

        Returns:
            str: The winner of the game.
        """
        if player_sum > 21:
            return "You busted! Dealer wins."
        elif dealer_sum > 21:
            return "Dealer busted! You win!"
        elif player_sum > dealer_sum:
            return "You win!"
        elif dealer_sum > player_sum:
            return "Dealer wins."
        else:
            return "It's a tie!"
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Economy module online')
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        pass
    
    @commands.command(name='balance', aliases=["bal"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def balance(self, ctx):
        '''
        Checks the balance of the user.
        '''
        self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        
        con = sqlite3.connect(economy_data)
        cur = con.cursor()
        # Retrieve balance from the database for the user
        user_id = ctx.author.id
        cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (user_id,))
        result = cur.fetchone()[0]
        balance = result if result else 0
        
        await ctx.reply(f"Your balance is {balance} coins.")
        cur.close()
        con.close()
    
    @commands.command(name="leaderboard", aliases=["lb"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def leaderboard(self, ctx):
        '''
        Make a list of the top oilers.
        '''
        self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        msg = ctx.reply("This command will put top oilers.")
        await ctx.message.delete(delay=MSG_DEL_DELAY)
        await msg.delete(delay=MSG_DEL_DELAY)
    
    
    @commands.command(name="daily")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def daily(self, ctx):
        '''
        Claim your daily reward of 100 coins.
        '''
        self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        user_id = ctx.author.id
        con = sqlite3.connect(economy_data)
        cur = con.cursor()
        
        cur.execute("SELECT balance, unix_time FROM economy_data WHERE user_id = ?", (user_id,))
        current_balance, last_daily = cur.fetchone()
        current_time = functions.get_unix_time()
        
        if current_time - last_daily < ONE_DAY:
            msg = await ctx.reply(f"Please wait {(ONE_DAY - (current_time - last_daily))/3600:.1f} hours before claiming your next daily reward.")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
            return
        else:
            new_balance = current_balance + 100
            cur.execute("UPDATE economy_data SET balance = ?, unix_time = ? WHERE user_id = ?", (new_balance, current_time, user_id))
            con.commit()
            cur.close()
            con.close()
            msg = await ctx.reply(f"You have claimed your daily reward of 100 coins. Your new balance is {new_balance} coins.")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.has_permissions(administrator=True)
    @commands.command(name="undaily", hidden=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def undaily(self, ctx, member:Union[discord.Member, int]=None):
        # '''
        # Reset the daily timer for yourself if no member is specified.
        # Sets all gamba scores to 0.
        # '''
        '''
        Resets the daily timer for the specified member or for the command invoker if no member is specified.
        Also sets all gamba scores (slots, blackjack, coinflip) to 0 for the specified member or for the command invoker if no member is specified.
        '''
        if member is None:
            user_id = ctx.author.id
            self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        elif isinstance(member, discord.Member):
            user_id = member.id
            self.check_user(member.id, member.name, ctx.guild.id, functions.get_unix_time())
        
        con = sqlite3.connect(economy_data)
        cur = con.cursor()
        cur.execute("UPDATE economy_data SET unix_time = ?, slots_wins = ?, slots_losses = ?, bj_wins = ?, bj_losses = ?, bj_ties = ?, cf_wins = ?, cf_losses = ? WHERE user_id = ?", (42069,0,0,0,0,0,0,0, user_id))
        con.commit()
        cur.close()
        con.close()
        msg = await ctx.reply("Daily reset.")
        await ctx.message.delete(delay=MSG_DEL_DELAY)
        await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(name='addtable', aliases=["at"], hidden=True)
    async def addtable(self, ctx, table_name:str, *columns):
        if ctx.author.id == owner_id:
            pass
    
    ##!GAMBA COMMANDS!##
    
    @commands.command(name="slots")
    async def slots(self, ctx, bet:int=10):
        '''
        Play slots with a bet and win big!
        '''
        self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        user_id = ctx.author.id
        con = sqlite3.connect(economy_data)
        cur = con.cursor()
        cur.execute("SELECT balance, slots_wins, slots_losses FROM economy_data WHERE user_id = ?", (user_id,))
        current_balance, slots_wins, slots_losses = cur.fetchone()
        
        if current_balance < bet:
            await ctx.reply(f"You don't have enough coins to play Slots with a bet of {bet}. Try waiting for your daily reward.", mention_author=False)
            return

        # Create a list of 3 lists, each containing 3 slot symbols
        slot_grid = [[random.choice(list(SLOT_SYMBOLS.keys())) for _ in range(3)] for _ in range(3)]

        # Create an empty embed
        embed = discord.Embed(title="Slot Machine", description=f"bet: {bet} coins", color=0x00ff00, timestamp=dt.datetime.utcnow())

        # Add the 3x3 grid of slot icons to the embed
        embed.add_field(name="\u200b", value=f"{slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n{slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n{slot_grid[2][0]} {slot_grid[2][1]} {slot_grid[2][2]}", inline=False)

        # Send the embed to the user
        embed.set_footer(text=botversion)
        msg = await ctx.reply(embed=embed)

        # Wait for a short period of time
        await asyncio.sleep(SLOTS_ROTATE_DELAY)

        # Loop through the animation 3 times
        for _ in range(6):
            # Edit the embed by moving the icons in the last row up by one position
            slot_grid[2] = slot_grid[1]
            slot_grid[1] = slot_grid[0]
            slot_grid[0] = [random.choice(list(SLOT_SYMBOLS.keys())) for _ in range(3)]

            # Add the 3x3 grid of slot icons to the embed
            embed.set_field_at(0, name="\u200b", value=f"{slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n{slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n{slot_grid[2][0]} {slot_grid[2][1]} {slot_grid[2][2]}", inline=False)

            # Send the edited embed to the user
            await msg.edit(embed=embed)

            # Wait for a short period of time
            await asyncio.sleep(SLOTS_ROTATE_DELAY)

        # Calculate the win or loss of the user based on the final grid of slot symbols
        payout = 0
        if slot_grid[0][0] == slot_grid[0][1] == slot_grid[0][2]:
            payout = SLOT_SYMBOLS[slot_grid[0][0]] * bet
        elif slot_grid[1][0] == slot_grid[1][1] == slot_grid[1][2]:
            payout = SLOT_SYMBOLS[slot_grid[1][0]] * bet
        elif slot_grid[2][0] == slot_grid[2][1] == slot_grid[2][2]:
            payout = SLOT_SYMBOLS[slot_grid[2][0]] * bet
        elif slot_grid[0][0] == slot_grid[1][1] == slot_grid[2][2]:
            payout = SLOT_SYMBOLS[slot_grid[0][0]] * (bet/2)
        elif slot_grid[0][2] == slot_grid[1][1] == slot_grid[2][0]:
            payout = SLOT_SYMBOLS[slot_grid[0][2]] * (bet/2)
        elif slot_grid[0][0] == slot_grid[1][0] == slot_grid[2][0]:
            payout = SLOT_SYMBOLS[slot_grid[0][0]] * (bet/3)
        elif slot_grid[0][1] == slot_grid[1][1] == slot_grid[2][1]:
            payout = SLOT_SYMBOLS[slot_grid[0][1]] * (bet/3)
        elif slot_grid[0][2] == slot_grid[1][2] == slot_grid[2][2]:
            payout = SLOT_SYMBOLS[slot_grid[0][2]] * (bet/3)

        # Update the user's balance, slots_wins, and slots_losses in the database
        if payout > 0:
            cur.execute("UPDATE economy_data SET balance = balance + ?, slots_wins = slots_wins + 1 WHERE user_id = ?", (payout, user_id))
            con.commit()
            slots_wins += 1
            result_embed = discord.Embed(title="Slot Machine", description=f"bet: {bet} coins\n{slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n{slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n{slot_grid[2][0]} {slot_grid[2][1]} \
                                                {slot_grid[2][2]}\n\nYou won {payout} coins! Your new balance is {current_balance + payout} coins.\nYou have won {slots_wins} times and lost {slots_losses} times.", color=0x00ff00, timestamp=dt.datetime.utcnow())
        else:
            cur.execute("UPDATE economy_data SET balance = balance - ?, slots_losses = slots_losses + 1 WHERE user_id = ?", (bet, user_id,))
            con.commit()
            slots_losses += 1
            result_embed = discord.Embed(title="Slot Machine", description=f"bet: {bet} coins\n{slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n{slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n{slot_grid[2][0]} {slot_grid[2][1]} \
                                                {slot_grid[2][2]}\n\nYou lost {bet} coins. Your new balance is {current_balance - bet} coins.\nYou have won {slots_wins} times and lost {slots_losses} times.", color=0xff0000, timestamp=dt.datetime.utcnow())

        # Send the result embed to the user
        result_embed.set_footer(text=botversion)
        await msg.edit(embed=result_embed)

        cur.close()
        con.close()

    @commands.command(name="coinflip", aliases=["cf"])
    async def coinflip(self, ctx, guess:str, bet:int=10):
        '''
        Flips a coin and gives you a chance to double your bet.
        Guess either heads / head / h, tails / tail / t.
        Bet defaults to 10 coins but you can enter your own amount.
        '''
        self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        if guess.lower() not in ["heads", "tails", "head", "tail", "h", "t", "edges", "edge", "e"]:
            msg = await ctx.reply("You must guess either `heads / head / h, tails / tail / t`.")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
            return
        elif guess.lower() in ["heads", "head", "h"]:
            guessed_coin = "Heads"
        elif guess.lower() in ["tails", "tail", "t"]:
            guessed_coin = "Tails"
        elif guess.lower() in ["edges", "edge", "e"]:
            guessed_coin = "Edge"
        
        user_id = ctx.author.id
        con = sqlite3.connect(economy_data)
        cur = con.cursor()
        cur.execute("SELECT balance, cf_wins, cf_losses FROM economy_data WHERE user_id = ?", (user_id,))
        current_balance, cf_wins, cf_losses = cur.fetchone()
        
        if current_balance < bet:
            msg = await ctx.reply(f"You don't have enough {currency_plural} to play Coinflip with a bet of {bet}. Try waiting for your daily reward.")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
            return
        elif bet == 0:
            msg = await ctx.reply("You can't bet 0 coins.")
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            await msg.delete(delay=MSG_DEL_DELAY)
            return
        outcome_possibilities = ["Heads", "Tails", "Edge"]
        outcome_weights = [0.49, 0.49, 0.02]
        coin = ''.join(random.choices(outcome_possibilities, outcome_weights)[0])
        
        embed = discord.Embed(title="Coinflip", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}\nGuess: {guessed_coin}", color=0x00ff00, timestamp=dt.datetime.utcnow())
        embed.add_field(name="Flipping coin", value='', inline=False)
        embed.set_footer(text=botversion)
        msg = await ctx.reply(embed=embed)
        
        dot = "."
        for i in range(1, 4):
            embed.set_field_at(0, name=f"Flipping coin{dot*i}", value="", inline=False)
            await msg.edit(embed=embed)
            await asyncio.sleep(1)
        
        # Calculate the win or loss of the user
        if guessed_coin == coin:
            payout = bet * 2
            cf_wins += 1
            cur.execute("UPDATE economy_data SET balance = balance + ?, cf_wins = cf_wins + 1 WHERE user_id = ?", (payout, user_id))
            con.commit()
            result_embed = discord.Embed(title="Coinflip", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}\nGuess: {guessed_coin}\nResult: {coin}\n\nCongratulations! You won {payout} {currency_plural}! \
                Your new balance is {current_balance + payout} {currency_plural}.\nYou have won {cf_wins} {'time' if cf_wins == 1 else 'times'} and lost {cf_losses} {'time' if cf_losses == 1 else 'times'}.", color=0x00ff00, timestamp=dt.datetime.utcnow())
        else:
            cf_losses += 1
            cur.execute("UPDATE economy_data SET balance = balance - ?, cf_losses = cf_losses + 1 WHERE user_id = ?", (bet, user_id))
            con.commit()
            result_embed = discord.Embed(title="Coinflip", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}\nGuess: {guessed_coin}\nResult: {coin}\n\nSorry, you lost {bet} {currency_singular if bet == 1 else currency_plural}. \
                Your new balance is {current_balance - bet} {currency_singular if current_balance - bet == 1 else currency_plural}.\nYou have won {cf_wins} {'time' if cf_wins == 1 else 'times'} and lost {cf_losses} {'time' if cf_losses == 1 else 'times'}.", color=0xff0000, timestamp=dt.datetime.utcnow())
        result_embed.set_footer(text=botversion)
        await msg.edit(embed=result_embed)
        cur.close()
        con.close()
    
    @commands.command(aliases=["bus"])
    async def bussen(self, ctx, bet:int=10):
        '''
        **Round 1:** 
        In the first round, you have to guess whether the first card you are dealt is red or black.
        
        **Round 2:**
        In the second round, you have to guess whether the card is higher or lower than the first card you received.
        
        **Round 3:** 
        In the third round, you have to guess whether the value of the card is inside or outside the two cards you already have.
        
        **Round 4:** 
        In the fourth round, you have to guess the suit of the 4th card. If you guess correctly, you win the game.
        '''
        four_random_cards = random.sample(list(CARDS.keys()), 4)
        card_back = BytesIO()
        card_row = BytesIO()
        card_1 = BytesIO()
        card_2 = BytesIO()
        # print(four_random_cards)
        pil_cardback = Image.open(CARDS['card_back'][4])
        pil_cardback.save(card_back, format='PNG')
        card_back.seek(0)
        round_1_card = discord.File(card_back, filename=f'{os.path.basename(CARDS["card_back"][4])}')
        
        
        round_1_embed = discord.Embed(title="Bussen", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}", color=0x00ff00, timestamp=dt.datetime.utcnow())
        round_1_embed.add_field(name="Round 1", value=f"In the first round, you are supposed to guess whether the first card you are dealt is red or black.", inline=False)
        round_1_embed.set_image(url=f'attachment://{os.path.basename(CARDS["card_back"][4])}')
        # embed.add_field(name="Round 2", value=f"In the second round, you have to guess whether the card is higher or lower than the first card you received.", inline=False)
        # embed.add_field(name="Round 3", value=f"In the third round, you have to guess whether the value of the card is inside or outside the two cards you already have.", inline=False)
        # embed.add_field(name="Round 4", value=f"In the fourth round, you have to guess the suit of the 4th card. If you guess correctly, you win the game.", inline=False)
        
        # round_2_cards = [discord.File(CARDS[four_random_cards[0]][4], filename=f'{os.path.basename(CARDS[four_random_cards[0]][4])}'), \
        #                 discord.File(CARDS['card_back'][4], filename=f'{os.path.basename(CARDS["card_back"][4])}')]
        
        # round_3_cards = [discord.File(CARDS[four_random_cards[0]][4], filename=f'{os.path.basename(CARDS[four_random_cards[0]][4])}'), \
        #                 discord.File(CARDS[four_random_cards[1]][4], filename=f'{os.path.basename(CARDS[four_random_cards[1]][4])}'), \
        #                 discord.File(CARDS['card_back'][4], filename=f'{os.path.basename(CARDS["card_back"][4])}')]
        
        # round_4_cards = [discord.File(CARDS[four_random_cards[0]][4], filename=f'{os.path.basename(CARDS[four_random_cards[0]][4])}'), \
        #                 discord.File(CARDS[four_random_cards[1]][4], filename=f'{os.path.basename(CARDS[four_random_cards[1]][4])}'), \
        #                 discord.File(CARDS[four_random_cards[2]][4], filename=f'{os.path.basename(CARDS[four_random_cards[2]][4])}'), \
        #                 discord.File(CARDS['card_back'][4], filename=f'{os.path.basename(CARDS["card_back"][4])}')]
        
        # result_cards = [discord.File(CARDS[four_random_cards[0]][4], filename=f'{os.path.basename(CARDS[four_random_cards[0]][4])}'), \
        #                 discord.File(CARDS[four_random_cards[1]][4], filename=f'{os.path.basename(CARDS[four_random_cards[1]][4])}'), \
        #                 discord.File(CARDS[four_random_cards[2]][4], filename=f'{os.path.basename(CARDS[four_random_cards[2]][4])}'), \
        #                 discord.File(CARDS[four_random_cards[3]][4], filename=f'{os.path.basename(CARDS[four_random_cards[3]][4])}')]
        
        
        round1_message = await ctx.reply(file=round_1_card, embed=round_1_embed, mention_author=False)
        
        await round1_message.add_reaction('🟥')
        await round1_message.add_reaction('⬛')
        
        check = lambda r, u: u == ctx.author and str(r.emoji) in ['🟥', '⬛']
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=15)
        except asyncio.TimeoutError:
            await round1_message.clear_reactions()
            await ctx.round1_message.delete()
            await round1_message.edit(content="Failed to respond.")
            return
        
        pil_card1 = Image.open(CARDS[four_random_cards[0]][4])
        if str(reaction.emoji) == '🟥':
            if CARDS[four_random_cards[0]][1] != 'red':
                await round1_message.delete()
                pil_card1.save(card_1, format='PNG')
                card_1.seek(0)
                result_card = discord.File(card_1, filename=f'{os.path.basename(CARDS[four_random_cards[0]][4])}')
                result_embed_round_1 = discord.Embed(title="Bussen", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}", color=0xff0000, timestamp=dt.datetime.utcnow())
                result_embed_round_1.add_field(name="Game over.", value=f"You failed to guess correctly.\nYou guessed: Red\nThe card was: {CARDS[four_random_cards[0]][3]} of {CARDS[four_random_cards[0]][0]}, which is {CARDS[four_random_cards[0]][1]}", inline=False)
                result_embed_round_1.set_image(url=f'attachment://{os.path.basename(CARDS[four_random_cards[0]][4])}')
                await ctx.reply(file=result_card, embed=result_embed_round_1, mention_author=False)
                return
        
        elif str(reaction.emoji) == '⬛':
            if CARDS[four_random_cards[0]][1] != 'black':
                await round1_message.delete()
                pil_card1.save(card_1, format='PNG')
                card_1.seek(0)
                result_card = discord.File(card_1, filename=f'{os.path.basename(CARDS[four_random_cards[0]][4])}')
                result_embed_round_1 = discord.Embed(title="Bussen", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}", color=0xff0000, timestamp=dt.datetime.utcnow())
                result_embed_round_1.add_field(name="Game over.", value=f"You failed to guess correctly.\nYou guessed: Black\nThe card was: {CARDS[four_random_cards[0]][3]} of {CARDS[four_random_cards[0]][0]}, which is {CARDS[four_random_cards[0]][1]}", inline=False)
                result_embed_round_1.set_image(url=f'attachment://{os.path.basename(CARDS[four_random_cards[0]][4])}')
                await ctx.reply(file=result_card, embed=result_embed_round_1, mention_author=False)
                return
        else:
            return
        
        pil_cardback_w, cardback_h = pil_cardback.size
        pil_card1_w = pil_card1.size[0]
        pil_cardrow = Image.new('RGBA', (pil_cardback_w + pil_card1_w, cardback_h), (0, 0, 0, 0))
        pil_cardrow.paste(pil_card1, (0, 0))
        pil_cardrow.paste(pil_cardback, (pil_card1_w, 0))
        pil_cardrow.save(card_row, format='PNG')
        card_row.seek(0)
        
        round_2_card = discord.File(card_row, filename=f'card_row.png')
        
        
        round_2_embed = discord.Embed(title="Bussen", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}", color=0x00ff00, timestamp=dt.datetime.utcnow())
        round_2_embed.add_field(name="Round 1 correct!", value=f'You correctly guessed the colour of the first card!\nThe first card was: {CARDS[four_random_cards[0]][3]} of {CARDS[four_random_cards[0]][0]}, which is {CARDS[four_random_cards[0]][1]}', inline=False)
        round_2_embed.add_field(name="Round 2", value=f"In the second round, you have to guess whether the card is higher or lower than the first card you received.", inline=False)
        round_2_embed.set_image(url=f'attachment://card_row.png')
        
        await round1_message.delete()
        round2_message = await ctx.reply(file=round_2_card, embed=round_2_embed, mention_author=False)
        
        await round2_message.add_reaction('🔼')
        await round2_message.add_reaction('🔽')
        
        check = lambda r, u: u == ctx.author and str(r.emoji) in ['🔼', '🔽']
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=15)
        except asyncio.TimeoutError:
            await round2_message.clear_reactions()
            await ctx.round2_message.delete()
            await round2_message.edit(content="Failed to respond.")
            return
    

    # @commands.command(name="blackjack", aliases=["bj"])
    # async def blackjack(self, ctx, bet:int=10):
    #     self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
    #     user_id = ctx.author.id
    #     con = sqlite3.connect(economy_data)
    #     cur = con.cursor()

    #     cur.execute("SELECT balance, bj_wins, bj_losses FROM economy_data WHERE user_id = ?", (user_id,))
    #     current_balance, bj_wins, bj_losses = cur.fetchone()

    #     # Check if user has enough balance to play
    #     if current_balance < bet:
    #         await ctx.send("You don't have enough balance to play blackjack.")
    #         return

    #     # Create a deck of cards and shuffle it
    #     deck = []
    #     suits = ['♠', '♥', '♦', '♣']
    #     ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    #     for suit in suits:
    #         for rank in ranks:
    #             deck.append(rank + suit)
    #     random.shuffle(deck)

    #     # Deal cards to player and dealer
    #     player_cards = [deck.pop(), deck.pop()]
    #     dealer_cards = [deck.pop(), deck.pop()]

    #     buttons_view = BlackjackButtons(ctx, player_cards, dealer_cards)

    #     # Send the initial message with the buttons view
    #     message = await ctx.send("Let's play blackjack!", view=buttons_view)

    #     # Wait for the user to click a button
    #     await buttons_view.wait()

    #     # Handle the user's choice
    #     if buttons_view.value == "hit":
    #         player_cards.append(deck.pop())
    #         player_sum = self.blackjack_calculate_sum(player_cards)
    #         if player_sum > 21:
    #             await ctx.send("You busted! Dealer wins.")
    #             bj_losses += 1
    #         else:
    #             dealer_sum = self.blackjack_dealer_turn(deck, dealer_cards)
    #             winner = self.blackjack_determine_winner(player_sum, dealer_sum)
    #             await ctx.send(winner)
    #             if winner == "You win!":
    #                 bj_wins += 1
    #             elif winner == "Dealer wins.":
    #                 bj_losses += 1
    #     elif buttons_view.value == "stand":
    #         dealer_sum = self.blackjack_dealer_turn(deck, dealer_cards)
    #         player_sum = self.blackjack_calculate_sum(player_cards)
    #         winner = self.blackjack_determine_winner(player_sum, dealer_sum)
    #         await ctx.send(winner)
    #         if winner == "You win!":
    #             bj_wins += 1
    #         elif winner == "Dealer wins.":
    #             bj_losses += 1

    #     # Update the message with the final scores
    #     await message.edit(content=f"Final score: You {bj_wins} - {bj_losses} Dealer")




async def setup(bot):
    await bot.add_cog(Economy(bot))

class BlackjackButtons(discord.ui.View):
    def __init__(self, ctx, player_cards, dealer_cards):
        super().__init__()
        self.ctx = ctx
        self.value = None

        # # Create an embed with the player's cards
        # player_embed = discord.Embed(title="Your Cards")
        # for card in player_cards:
        #     card_image = deck_of_cards.get_card_image(card)
        #     player_embed.set_image(url=card_image)

        # # Create an embed with the dealer's cards
        # dealer_embed = discord.Embed(title="Dealer's Cards")
        # for card in dealer_cards:
        #     card_image = deck_of_cards.get_card_image(card)
        #     dealer_embed.set_image(url=card_image)

        # Add the embeds to the view
        # self.add_item(discord.ui.MessageButton(label="Hit", style=discord.ButtonStyle.green, custom_id="hit", emoji="👊"))
        # self.add_item(discord.ui.MessageButton(label="Stand", style=discord.ButtonStyle.red, custom_id="stand", emoji="🛑"))
        # self.add_item(discord.ui.MessageEmbedView(embed=player_embed))
        # self.add_item(discord.ui.MessageEmbedView(embed=dealer_embed))

    @discord.ui.button(custom_id="hit", style=discord.ButtonStyle.green, label="Hit", emoji="👊")
    async def hit(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "hit"
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(custom_id="stand", style=discord.ButtonStyle.red,label="stand", emoji="🛑")
    async def stand(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "stand"
        self.stop()
        await interaction.response.defer()
# class BlackjackButtons(discord.ui.View):
#     def __init__(self, ctx):
#         super().__init__()
#         self.ctx = ctx
#         self.value = None

#     @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, custom_id="hit")
#     async def hit(self, button: discord.ui.Button, interaction: discord.Interaction):
#         self.value = "hit"
#         self.stop()

#     @discord.ui.button(label="Stand", style=discord.ButtonStyle.red, custom_id="stand")
#     async def stand(self, button: discord.ui.Button, interaction: discord.Interaction):
#         self.value = "stand"
#         self.stop()


# @commands.command(name="blackjack", aliases=["bj"])
#     async def blackjack(self, ctx):
#         self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
#         user_id = ctx.author.id
#         con = sqlite3.connect(economy_data)
#         cur = con.cursor()

#         cur.execute("SELECT balance, bj_wins, bj_losses FROM economy_data WHERE user_id = ?", (user_id,))
#         current_balance, bj_wins, bj_losses = cur.fetchone()

#         # Check if user has enough balance to play
#         if current_balance < 10:
#             await ctx.send("You don't have enough balance to play blackjack.")
#             return

#         # Create a deck of cards and shuffle it
#         deck = []
#         suits = ['♠', '♥', '♦', '♣']
#         ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
#         for suit in suits:
#             for rank in ranks:
#                 deck.append(rank + suit)
#         random.shuffle(deck)

#         # Deal cards to player and dealer
#         player_cards = [deck.pop(), deck.pop()]
#         dealer_cards = [deck.pop(), deck.pop()]

#         # Calculate the sum of player's cards
#         player_sum = self.blackjack_calculate_sum(player_cards)

#         # Display initial game state and wait for player's decision
#         buttons = BlackjackButtons(ctx)
#         player_card_string = " ".join(player_cards)
#         dealer_card_string = dealer_cards[0]
#         embed = discord.Embed(title="Blackjack", description=f"Your cards: {player_card_string}.\nDealer's card: {dealer_card_string}.")
#         message = await ctx.send(embed=embed, view=buttons)
#         await buttons.wait()
#         decision = buttons.value

#         # Loop for player's actions
#         while (decision == "hit" or decision == "split") and player_sum < 21:
#             if decision == "hit":
#                 player_cards.append(deck.pop())
#                 player_sum = self.blackjack_calculate_sum(player_cards)
            
#             elif decision == "split":
#                 if len(player_cards) != 2 or player_cards[0][0] != player_cards[1][0]:
#                     await ctx.send("Split is only available when you have two cards of the same rank.")
#                     return
#                 if current_balance < 10:
#                     await ctx.send("You don't have enough balance to Split.")
#                     return
#                 split = True
#                 split_cards = [player_cards.pop(), deck.pop()]
#                 player_sum = self.blackjack_calculate_sum(player_cards)
#                 split_sum = self.blackjack_calculate_sum(split_cards)
#                 current_balance -= 10  # Additional bet for Split

#                 # Deal cards to the two split hands
#                 player_cards.append(deck.pop())
#                 split_cards.append(deck.pop())

#                 # Calculate the sum of the two split hands
#                 player_sum = self.blackjack_calculate_sum(player_cards)
#                 split_sum = self.blackjack_calculate_sum(split_cards)

#                 # Display the two split hands and wait for player's decision
#                 buttons = BlackjackButtons(ctx)
#                 player_card_string = " ".join(player_cards)
#                 split_card_string = " ".join(split_cards)
#                 dealer_card_string = dealer_cards[0]
#                 embed = discord.Embed(title="Blackjack", description=f"Your cards: {player_card_string}.\nDealer's card: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                 message = await ctx.send(embed=embed, view=buttons)
#                 await buttons.wait()
#                 decision = buttons.value

#                 # Loop for player's actions on the first split hand
#                 while (decision == "hit" or decision == "stand") and player_sum < 21:
#                     if decision == "hit":
#                         player_cards.append(deck.pop())
#                         player_sum = self.blackjack_calculate_sum(player_cards)
                    
#                     # Update the embed and wait for the next decision
#                     player_card_string = " ".join(player_cards)
#                     split_card_string = " ".join(split_cards)
#                     embed = discord.Embed(title="Blackjack", description=f"Your cards: {player_card_string}.\nDealer's card: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     await message.edit(embed=embed)
#                     await buttons.wait()
#                     decision = buttons.value

#                 # Loop for player's actions on the second split hand
#                 while (decision == "hit" or decision == "stand") and split_sum < 21:
#                     if decision == "hit":
#                         split_cards.append(deck.pop())
#                         split_sum = self.blackjack_calculate_sum(split_cards)
                    
#                     # Update the embed and wait for the next decision
#                     player_card_string = " ".join(player_cards)
#                     split_card_string = " ".join(split_cards)
#                     embed = discord.Embed(title="Blackjack", description=f"Your cards: {player_card_string}.\nDealer's card: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     await message.edit(embed=embed)
#                     await buttons.wait()
#                     decision = buttons.value

#                 # Determine the winner for the first split hand
#                 if player_sum > 21:
#                     embed = discord.Embed(title="Blackjack", description=f"You busted on your first split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance = current_balance - 10
#                     bj_losses += 1
#                 elif dealer_sum > 21:
#                     embed = discord.Embed(title="Blackjack", description=f"Dealer busted on your first split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance = current_balance + 10
#                     bj_wins += 1
#                 elif player_sum > dealer_sum:
#                     embed = discord.Embed(title="Blackjack", description=f"You won on your first split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance = current_balance + 10
#                     bj_wins += 1
#                 elif dealer_sum > player_sum:
#                     embed = discord.Embed(title="Blackjack", description=f"You lost on your first split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance = current_balance - 10
#                     bj_losses += 1
#                 else:
#                     embed = discord.Embed(title="Blackjack", description=f"It's a tie on your first split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance = current_balance

#                 # Update user's balance and stats in the database
#                 cur.execute("UPDATE economy_data SET balance = ?, bj_wins = ?, bj_losses = ? WHERE user_id = ?", (new_balance, bj_wins, bj_losses, user_id))
#                 con.commit()

#                 # Determine the winner for the second split hand
#                 if split_sum > 21:
#                     embed = discord.Embed(title="Blackjack", description=f"You busted on your second split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance -= 10
#                     bj_losses += 1
#                 elif dealer_sum > 21:
#                     embed = discord.Embed(title="Blackjack", description=f"Dealer busted on your second split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance += 10
#                     bj_wins += 1
#                 elif split_sum > dealer_sum:
#                     embed = discord.Embed(title="Blackjack", description=f"You won on your second split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance += 10
#                     bj_wins += 1
#                 elif dealer_sum > split_sum:
#                     embed = discord.Embed(title="Blackjack", description=f"You lost on your second split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance -= 10
#                     bj_losses += 1
#                 else:
#                     embed = discord.Embed(title="Blackjack", description=f"It's a tie on your second split hand!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.\n\nYour split cards: {split_card_string}.")
#                     new_balance = current_balance

#                 # Update user's balance and stats in the database
#                 cur.execute("UPDATE economy_data SET balance = ?, bj_wins = ?, bj_losses = ? WHERE user_id = ?", (new_balance, bj_wins, bj_losses, user_id))
#                 con.commit()
#                 cur.close()
#                 con.close()

#                 # Edit the embed with the final message
#                 await message.edit(embed=embed, view=None)
#                 return

#             # Update the embed and wait for the next decision
#             player_card_string = " ".join(player_cards)
#             dealer_card_string = dealer_cards[0]
#             embed = discord.Embed(title="Blackjack", description=f"Your cards: {player_card_string}.\nDealer's card: {dealer_card_string}.")
#             await message.edit(embed=embed)
#             await buttons.wait()
#             decision = buttons.value

#         # Calculate the sum of dealer's cards
#         dealer_sum = self.blackjack_calculate_sum(dealer_cards)

#         # Dealer hits until their sum is greater than or equal to 17
#         while dealer_sum < 17:
#             dealer_cards.append(deck.pop())
#             dealer_sum = self.blackjack_calculate_sum(dealer_cards)

#         # Determine the winner
#         if player_sum > 21:
#             embed = discord.Embed(title="Blackjack", description=f"You busted!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.")
#             new_balance = current_balance - 10
#             bj_losses += 1
#         elif dealer_sum > 21:
#             embed = discord.Embed(title="Blackjack", description=f"Dealer busted!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.")
#             new_balance = current_balance + 10
#             bj_wins += 1
#         elif player_sum > dealer_sum:
#             embed = discord.Embed(title="Blackjack", description=f"You won!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.")
#             new_balance = current_balance + 10
#             bj_wins += 1
#         elif dealer_sum > player_sum:
#             embed = discord.Embed(title="Blackjack", description=f"You lost!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.")
#             new_balance = current_balance - 10
#             bj_losses += 1
#         else:
#             embed = discord.Embed(title="Blackjack", description=f"It's a tie!\nYour cards: {player_card_string}.\nDealer's cards: {dealer_card_string}.")
#             new_balance = current_balance

#         # Update user's balance and stats in the database
#         cur.execute("UPDATE economy_data SET balance = ?, bj_wins = ?, bj_losses = ? WHERE user_id = ?", (new_balance, bj_wins, bj_losses, user_id))
#         con.commit()
#         cur.close()
#         con.close()

#         # Edit the embed with the final message
#         await message.edit(embed=embed, view=None)
