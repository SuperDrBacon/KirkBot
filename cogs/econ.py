import asyncio
import os
import random
import sqlite3
from configparser import ConfigParser
from datetime import datetime, timezone
from io import BytesIO
from typing import List, Tuple, Union

import aiosqlite
import discord
from discord.ext import commands
from discord.ui import Button, View, button
from PIL import Image, ImageDraw, ImageFont

import cogs.utils.functions as functions

ospath = os.path.abspath(os.getcwd())
cardspath = rf'{ospath}/playingcards/'
dicepath = rf'{ospath}/dice/'
economy_data = rf'{ospath}/cogs/economy_data.db'
permissions_data = rf'{ospath}/cogs/permissions_data.db'

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
    'diamonds_10':      ('Diamonds',  'red',    '♦',    '10',       f'{cardspath}diamonds_10.png'),
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

# Color variants for dice faces
DICE = {
    # Each dice number has color variants
    1: {
        'white': f'{dicepath}one_white.png',
        'red': f'{dicepath}one_red.png',
        'green': f'{dicepath}one_green.png'
    },
    2: {
        'white': f'{dicepath}two_white.png',
        'red': f'{dicepath}two_red.png',
        'green': f'{dicepath}two_green.png'
    },
    3: {
        'white': f'{dicepath}three_white.png',
        'red': f'{dicepath}three_red.png',
        'green': f'{dicepath}three_green.png'
    },
    4: {
        'white': f'{dicepath}four_white.png',
        'red': f'{dicepath}four_red.png',
        'green': f'{dicepath}four_green.png'
    },
    5: {
        'white': f'{dicepath}five_white.png',
        'red': f'{dicepath}five_red.png',
        'green': f'{dicepath}five_green.png'
    },
    6: {
        'white': f'{dicepath}six_white.png',
        'red': f'{dicepath}six_red.png',
        'green': f'{dicepath}six_green.png'
    }
}

# Existing Blackjack-related variables and constants
CARD_SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
CARD_RANKS = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']
CARD_VALUES = {'Ace': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'Jack': 10, 'Queen': 10, 'King': 10}

class Economy(commands.Cog):
    '''
    This module provides commands and functionality related to the economy system of the bot.
    '''
    def __init__(self, bot):
        self.bot = bot
        # asyncio.create_task(self.add_ttt_columns())  # Add new columns when cog loads
    
    # async def add_ttt_columns(self):
    #     async with aiosqlite.connect(economy_data) as con:
    #         async with con.cursor() as cur:
    #             # Check if columns already exist to avoid errors
    #             await cur.execute("PRAGMA table_info(economy_data)")
    #             columns = [info[1] for info in await cur.fetchall()]
                
    #             # Add columns if they don't exist
    #             if "TTT_WINS" not in columns:
    #                 await cur.execute("ALTER TABLE economy_data ADD COLUMN TTT_WINS INTEGER DEFAULT 0")
    #             if "TTT_LOSSES" not in columns:
    #                 await cur.execute("ALTER TABLE economy_data ADD COLUMN TTT_LOSSES INTEGER DEFAULT 0")
    #             if "TTT_TIES" not in columns:
    #                 await cur.execute("ALTER TABLE economy_data ADD COLUMN TTT_TIES INTEGER DEFAULT 0")
                    
    #         await con.commit()
    
    def economy_commands_enabled():
        """
        Custom check that verifies if economy commands are enabled in the channel.
        """
        async def predicate(ctx):
            cog = ctx.bot.get_cog("Economy")
            if cog:
                return await cog.check_channel_permissions(ctx)
            return True
        return commands.check(predicate)
    
    async def check_channel_permissions(self, ctx):
        """
        Check if economy commands are enabled in the current channel.
        
        Args:
            ctx: The command context with guild_id and channel_id
            
        Returns:
            bool: True if economy commands are enabled in the channel, False otherwise
        """
        if ctx.guild is None:  # Skip check in DMs
            return True
            
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        
        async with aiosqlite.connect(permissions_data) as con:
            async with con.execute('SELECT enabled FROM economy WHERE server_id = ? AND channel_id = ?', (guild_id, channel_id)) as cursor:
                result = await cursor.fetchone()
                channel_enabled = result is not None and result[0]
        
        if not channel_enabled:
            await ctx.reply("Economy commands are disabled in this channel.", delete_after=MSG_DEL_DELAY)
            await ctx.message.delete(delay=MSG_DEL_DELAY)
            return False
        
        return True
    
    async def check_user(self, user_id:int, user_name:str, server_id:int, unix_time:int):
        '''
        Checks if the user exists in the database and adds them if they don't.
        
        Args:
            user_id (int): The ID of the user.
            user_name (str): The name of the user.
            server_id (int): The ID of the server.
            unix_time (int): The current Unix time.
        '''
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT user_id FROM economy_data WHERE user_id = ?", (user_id,))
                result = await cur.fetchone()
        if not result:
            await self.add_user(user_id, user_name, server_id, unix_time)
    
    async def add_user(self, user_id:int, user_name:str, server_id:int, unix_time:int):
        '''
        Adds a new user to the database.
        
        Args:
            user_id (int): The ID of the user.
            user_name (str): The name of the user.
            server_id (int): The ID of the server.
            unix_time (int): The current Unix time.
        '''
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
                CF_LOSSES,
                TTT_WINS,
                TTT_LOSSES,
                TTT_TIES
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

        data_tuple = (user_id, user_name, server_id, unix_time, STARTING_BALANCE, STARTING_BANK, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute(data_to_insert, data_tuple)
            await con.commit()
    
    async def get_user_balance(self, user_id:int):
        '''
        Retrieves the balance of a user from the database.
        
        Args:
            user_id (int): The ID of the user.
            server_id (int): The ID of the server.
        
        Returns:
            int: The balance of the user.
        '''
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (user_id,))
                result = await cur.fetchone()
        
        balance = result[0] if result else 0
        return balance
    
    
    def calculate_hand_value(self, hand):
        """Calculate the value of a blackjack hand."""
        value = 0
        aces = 0
        
        for card in hand:
            rank = card[0]
            if rank == 'Ace':
                aces += 1
                value += 11
            else:
                value += CARD_VALUES[rank]
        
        # Adjust for aces if needed
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value

    def create_blackjack_embed(self, player_hand, dealer_hand, player_value, dealer_value, bet, hide_dealer_card=True, balance=0):
        """Create a beautiful embed for the blackjack game with card images."""
        embed = discord.Embed(
            title="Blackjack",
            description=f"Bet: {bet} {currency_singular if bet == 1 else currency_plural}",
            color=0x00ff00,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Player's hand section
        player_cards_str = []
        for card in player_hand:
            rank, suit = card
            player_cards_str.append(f"{rank} of {suit}")
        
        embed.add_field(
            name=f"Your Hand ({player_value})",
            value="\n".join(player_cards_str),
            inline=True
        )
        
        # Dealer's hand section
        if hide_dealer_card:
            dealer_cards_str = [f"{dealer_hand[0][0]} of {dealer_hand[0][1]}", "?? of ??"]
        else:
            dealer_cards_str = [f"{card[0]} of {card[1]}" for card in dealer_hand]
        
        embed.add_field(
            name=f"Dealer's Hand ({dealer_value})",
            value="\n".join(dealer_cards_str),
            inline=True
        )
        
        # Add player card images as an attachment
        card_image = self.create_hand_image(player_hand, dealer_hand, hide_dealer_card)
        
        # Convert the PIL image to a bytes object
        with BytesIO() as image_binary:
            card_image.save(image_binary, 'PNG')
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename="blackjack_cards.png")
            embed.set_image(url="attachment://blackjack_cards.png")
        
        embed.add_field(name="Balance", value=f"{balance} {currency_plural}", inline=False)
        embed.set_footer(text=botversion)
        
        return embed, file

    def create_hand_image(self, player_hand, dealer_hand, hide_dealer_card=True):
        """Create a combined image of all cards in player's and dealer's hands."""
        # Set up image dimensions
        card_width = 100  # We'll resize the card images
        card_height = 145
        card_spacing = 10
        vertical_spacing = 40
        
        # Calculate total width needed
        max_cards = max(len(player_hand), len(dealer_hand))
        total_width = (max_cards * card_width) + ((max_cards - 1) * card_spacing)
        total_height = (2 * card_height) + vertical_spacing
        
        # Create a new blank image
        combined_image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(combined_image)
        
        # Load a font
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except IOError:
            font = ImageFont.load_default()
        
        # Add labels
        draw.text((10, 5), "Dealer", fill=(255, 255, 255), font=font)
        draw.text((10, card_height + vertical_spacing - 20), "Player", fill=(255, 255, 255), font=font)
        
        # Add player cards at the bottom
        x_offset = 0
        for card in player_hand:
            rank, suit = card
            card_key = self.get_card_key(rank, suit)
            
            if card_key in CARDS:
                card_path = CARDS[card_key][4]
                try:
                    card_image = Image.open(card_path)
                    card_image = card_image.resize((card_width, card_height))
                    combined_image.paste(card_image, (x_offset, total_height - card_height))
                    x_offset += card_width + card_spacing
                except Exception as e:
                    print(f"Error loading card image: {e}")
        
        # Add dealer cards at the top
        x_offset = 0
        for i, card in enumerate(dealer_hand):
            # If hiding the second card, use card back
            if i > 0 and hide_dealer_card:
                card_key = 'card_back'
            else:
                rank, suit = card
                card_key = self.get_card_key(rank, suit)
                
            if card_key in CARDS:
                card_path = CARDS[card_key][4]
                try:
                    card_image = Image.open(card_path)
                    card_image = card_image.resize((card_width, card_height))
                    combined_image.paste(card_image, (x_offset, 0))
                    x_offset += card_width + card_spacing
                except Exception as e:
                    print(f"Error loading card image: {e}")
        
        return combined_image

    def get_card_key(self, rank, suit):
        """Convert a rank and suit to the corresponding key in the CARDS dictionary."""
        # Handle special cases
        rank_lower = rank.lower()
        suit_lower = suit.lower()
        
        # The CARDS dictionary keys are in the format suit_rank
        return f"{suit_lower}_{rank_lower}"

    def dealer_play(self, deck, dealer_hand):
        """Dealer plays their hand according to standard rules."""
        dealer_value = self.calculate_hand_value(dealer_hand)
        
        # Dealer must hit on 16 or lower, stand on 17 or higher
        while dealer_value < 17:
            dealer_hand.append(deck.pop())
            dealer_value = self.calculate_hand_value(dealer_hand)
        
        return dealer_hand, dealer_value
    
    def evaluate_dice_hand(self, dice):
        """Evaluate the dice hand and return hand type and multiplier"""
        # Sort the dice for easier evaluation
        dice.sort()
        
        # Count occurrences of each value
        counts = {}
        for die in dice:
            counts[die] = counts.get(die, 0) + 1
        
        # Get the counts as a list and sort
        values = list(counts.values())
        values.sort(reverse=True)
        
        # Check for five of a kind
        if values[0] == 5:
            return "Five of a Kind", 50
            
        # Check for four of a kind
        if values[0] == 4:
            return "Four of a Kind", 10
            
        # Check for full house (3 of a kind + pair)
        if values[0] == 3 and values[1] == 2:
            return "Full House", 7
            
        # Check for straight (5 consecutive values)
        if len(counts) == 5 and max(dice) - min(dice) == 4:
            return "Straight", 5
            
        # Check for three of a kind
        if values[0] == 3:
            return "Three of a Kind", 3
            
        # Check for two pair
        if values[0] == 2 and values[1] == 2:
            return "Two Pair", 2
            
        # Check for one pair
        if values[0] == 2:
            return "Pair", 1
            
        # High card - no win
        return "Nothing", 0
    
    def create_dice_image(self, dice_values, hand_type="Nothing"):
        """Create an image with the dice values arranged in a row with colored dice for patterns"""
        original_dice_size = 35  # Original dice image size
        scale_factor = 2  # Make images 2 times bigger
        dice_size = int(original_dice_size * scale_factor)  # Scaled dice size
        padding = int(5 * scale_factor)  # Scale padding proportionally
        
        # Calculate total width and height
        total_width = (dice_size * len(dice_values)) + ((len(dice_values) - 1) * padding)
        total_height = dice_size
        
        # Create a new blank image
        combined_image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
        
        # Determine which dice should be colored based on the hand type
        dice_colors = {}  # Dictionary to track which dice should be which color
        
        # Count occurrences of each value
        counts = {}
        for die in dice_values:
            counts[die] = counts.get(die, 0) + 1
        
        # Default all dice to white
        for i, value in enumerate(dice_values):
            dice_colors[i] = 'white'
        
        # Assign colors based on hand patterns
        if hand_type == "Five of a Kind":
            # All dice green
            for i in range(len(dice_values)):
                dice_colors[i] = 'green'
                
        elif hand_type == "Four of a Kind":
            # Four matching dice green
            for value, count in counts.items():
                if count == 4:
                    for i, die in enumerate(dice_values):
                        if die == value:
                            dice_colors[i] = 'green'
                            
        elif hand_type == "Full House":
            # Three of a kind in green, pair in red
            three_value = None
            two_value = None
            for value, count in counts.items():
                if count == 3:
                    three_value = value
                elif count == 2:
                    two_value = value
                    
            for i, die in enumerate(dice_values):
                if die == three_value:
                    dice_colors[i] = 'green'
                elif die == two_value:
                    dice_colors[i] = 'red'
                    
        elif hand_type == "Straight":
            # All dice green for straight
            for i in range(len(dice_values)):
                dice_colors[i] = 'green'
                
        elif hand_type == "Three of a Kind":
            # Three matching dice in green
            for value, count in counts.items():
                if count == 3:
                    for i, die in enumerate(dice_values):
                        if die == value:
                            dice_colors[i] = 'green'
                            
        elif hand_type == "Two Pair":
            # First pair in green, second pair in red
            pairs = [value for value, count in counts.items() if count == 2]
            if len(pairs) >= 2:
                first_pair = pairs[0]
                second_pair = pairs[1]
                
                for i, die in enumerate(dice_values):
                    if die == first_pair:
                        dice_colors[i] = 'green'
                    elif die == second_pair:
                        dice_colors[i] = 'red'
                        
        elif hand_type == "Pair":
            # Pair in green
            for value, count in counts.items():
                if count == 2:
                    for i, die in enumerate(dice_values):
                        if die == value:
                            dice_colors[i] = 'green'
        
        # Add each dice image
        x_offset = 0
        for i, value in enumerate(dice_values):
            try:
                # Get the color for this die position
                color = dice_colors.get(i, 'white')
                
                # Use the specified color version or fall back to default
                if color in DICE[value]:
                    dice_path = DICE[value][color]
                else:
                    dice_path = DICE[value]['default']
                    
                dice_image = Image.open(dice_path)
                
                # Resize to our new scaled size
                dice_image = dice_image.resize((dice_size, dice_size))
                combined_image.paste(dice_image, (x_offset, 0))
                x_offset += dice_size + padding
            except Exception as e:
                print(f"Error loading dice image: {e}")
        
        return combined_image
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Economy module online')
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        pass
    
    @commands.command(name='balance', aliases=["bal"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def balance(self, ctx):
        '''
        Checks the balance of the user.
        '''
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (ctx.author.id,))
                result = await cur.fetchone()
        
        balance = result[0] if result else 0
        await ctx.reply(f"Your balance is {balance} {currency_singular if balance == 1 else currency_plural}.")
    
    @commands.command(name="leaderboard", aliases=["lb"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def leaderboard(self, ctx):
        '''
        Make a list of the top 10 richest players.
        '''
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        
        # Query to get top 10 users with highest balance
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT user_id, username, balance FROM economy_data ORDER BY balance DESC LIMIT 10")
                top_users = await cur.fetchall()
        
        if not top_users:
            await ctx.reply("No users found in the economy database.")
            return
        
        # Create an embed for the leaderboard
        embed = discord.Embed(
            title="💰 Richest Users Leaderboard 💰",
            color=0xFFD700,  # Gold color
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add each user to the leaderboard
        for i, (user_id, username, balance) in enumerate(top_users, 1):
            # Try to get the user from Discord to use their current username
            try:
                user = await self.bot.fetch_user(user_id)
                display_name = user.name
            except:
                # Fall back to the stored username if we can't fetch the user
                display_name = username
            
            # Add medal emojis for top 3
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            embed.add_field(
                name=f"{medal} {display_name}",
                value=f"{balance} {currency_plural}",
                inline=False
            )
        
        embed.set_footer(text=botversion)
        await ctx.reply(embed=embed)
    
    @commands.command(name="daily")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def daily(self, ctx):
        '''
        Claim your daily reward of 100 coins.
        '''
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        user_id = ctx.author.id
        current_time = functions.get_unix_time()
        
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance, unix_time FROM economy_data WHERE user_id = ?", (user_id,))
                current_balance, last_daily = await cur.fetchone()
                
                if current_time - last_daily < ONE_DAY:
                    msg = await ctx.reply(f"Please wait {(ONE_DAY - (current_time - last_daily))/3600:.1f} hours before claiming your next daily reward.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                else:
                    new_balance = current_balance + 100
                    await cur.execute("UPDATE economy_data SET balance = ?, unix_time = ? WHERE user_id = ?", (new_balance, current_time, user_id))
                    msg = await ctx.reply(f"You have claimed your daily reward of 100 {currency_plural}. Your new balance is {new_balance} {currency_plural}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
            await con.commit()
    
    @commands.command(name="undaily", hidden=True) #aliases=["add"],
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def undaily(self, ctx, member:Union[discord.Member, int]=None):
        '''
        Resets the daily timer for the specified member or for the command invoker if no member is specified.
        Can also set all gamba scores (slots, blackjack, coinflip) to 0 for the specified member or for the command invoker if no member is specified.
        '''
        if member is None:
            user_id = ctx.author.id
            await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        elif isinstance(member, discord.Member):
            user_id = member.id
            await self.check_user(member.id, member.name, ctx.guild.id, functions.get_unix_time())
        
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("UPDATE economy_data SET unix_time = ?, balance = ? WHERE user_id = ?", (42069, 10000, user_id))
                # await cur.execute("UPDATE economy_data SET unix_time = ?, slots_wins = ?, slots_losses = ?, bj_wins = ?, bj_losses = ?, bj_ties = ?, cf_wins = ?, cf_losses = ? WHERE user_id = ?", (42069,0,0,0,0,0,0,0, user_id))
            await con.commit()
        
        msg = await ctx.reply("Daily reset.")
        await ctx.message.delete(delay=MSG_DEL_DELAY)
        await msg.delete(delay=MSG_DEL_DELAY)
    
    @commands.command(name="gamestats", aliases=["stats"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def gamestats(self, ctx):
        """View your game statistics."""
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        user_id = ctx.author.id
        
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute(
                    "SELECT slots_wins, slots_losses, bj_wins, bj_losses, bj_ties, cf_wins, cf_losses, ttt_wins, ttt_losses, ttt_ties " +
                    "FROM economy_data WHERE user_id = ?", 
                    (user_id,)
                )
                stats = await cur.fetchone()
                
        if stats:
            slots_wins, slots_losses, bj_wins, bj_losses, bj_ties, cf_wins, cf_losses, ttt_wins, ttt_losses, ttt_ties = stats
            
            embed = discord.Embed(
                title="Game Statistics",
                color=0x00FFFF,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Calculate win rates
            slots_total = slots_wins + slots_losses
            slots_rate = f"{(slots_wins / slots_total * 100) if slots_total > 0 else 0:.1f}%"
            
            bj_total = bj_wins + bj_losses + bj_ties
            bj_rate = f"{(bj_wins / (bj_total - bj_ties) * 100) if (bj_total - bj_ties) > 0 else 0:.1f}%"
            
            cf_total = cf_wins + cf_losses
            cf_rate = f"{(cf_wins / cf_total * 100) if cf_total > 0 else 0:.1f}%"
            
            ttt_total = ttt_wins + ttt_losses + ttt_ties
            ttt_rate = f"{(ttt_wins / (ttt_total - ttt_ties) * 100) if (ttt_total - ttt_ties) > 0 else 0:.1f}%"
            
            # Add slots stats
            embed.add_field(
                name="🎰 Slots",
                value=f"Wins: {slots_wins}\nLosses: {slots_losses}\nWin Rate: {slots_rate}",
                inline=True
            )
            
            # Add blackjack stats
            embed.add_field(
                name="🃏 Blackjack",
                value=f"Wins: {bj_wins}\nLosses: {bj_losses}\nTies: {bj_ties}\nWin Rate: {bj_rate}",
                inline=True
            )
            
            # Add coinflip stats
            embed.add_field(
                name="🪙 Coinflip",
                value=f"Wins: {cf_wins}\nLosses: {cf_losses}\nWin Rate: {cf_rate}",
                inline=True
            )
            # Add tic-tac-toe stats
            embed.add_field(
                name="❌⭕ Tic-Tac-Toe",
                value=f"Wins: {ttt_wins}\nLosses: {ttt_losses}\nTies: {ttt_ties}\nWin Rate: {ttt_rate}",
                inline=True
            )
            embed.set_footer(text=botversion)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("No game statistics found.")
    
    
    
    #!GAMBA COMMANDS
    
    @commands.command(name="slots")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def slots(self, ctx, bet:float=10):
        '''
        - The `slots` command allows users to play a slot machine game. The user bets a certain amount, and if the slots line up in a certain way, they win a multiple of their bet. 
        - The possible slot outcomes depend on their corresponding multipliers, which are defined as follows:
         - "🍒": 2x multiplier
         - "🍊": 3x multiplier
         - "🍋": 4x multiplier
         - "🍉": 5x multiplier
         - "🍇": 6x multiplier
         - "🍎": 7x multiplier
         - "🍓": 8x multiplier
         - "🍍": 10x multiplier
         - "💰": 20x multiplier
        
        1. If all 3 symbols in the top, middle or bottom row match, the payout is the multiplier for that symbol times the bet amount.
        2. If all 3 symbols in the left, middle or right column match, the payout is the multiplier for that symbol times the bet amount.
        3. If all 3 symbols in the either diagonal match, the payout is the multiplier for that symbol times 1/2 the bet amount.
        '''
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        user_id = ctx.author.id
        
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance, slots_wins, slots_losses FROM economy_data WHERE user_id = ?", (user_id,))
                current_balance, slots_wins, slots_losses = await cur.fetchone()
                
                if current_balance < bet:
                    msg = await ctx.reply(f"You don't have enough {currency_plural} to play Slots with a bet of {bet} {currency_singular if bet == 1 else currency_plural}. Your current balance is only {current_balance} {currency_singular if current_balance == 1 else currency_plural}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                elif bet <= 0:
                    msg = await ctx.reply(f"You can't bet {bet} {currency_plural}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                
                slot_grid = [[random.choice(list(SLOT_SYMBOLS.keys())) for _ in range(3)] for _ in range(3)]
                embed = discord.Embed(title="Slot Machine", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}", color=0x00ff00, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="\u200b",  value=f"{slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n\
                                                        {slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n\
                                                        {slot_grid[2][0]} {slot_grid[2][1]} {slot_grid[2][2]}", inline=False)
                
                embed.set_footer(text=botversion)
                msg = await ctx.reply(embed=embed)
                await asyncio.sleep(SLOTS_ROTATE_DELAY)
                
                for _ in range(6):
                    # Edit the embed by moving the icons in the last row down by one position
                    slot_grid[2] = slot_grid[1]
                    slot_grid[1] = slot_grid[0]
                    slot_grid[0] = [random.choice(list(SLOT_SYMBOLS.keys())) for _ in range(3)]
                    
                    # edit the 3x3 grid of slot icons to the embed
                    embed.set_field_at(0,name="\u200b", value=f"{slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n\
                                                                {slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n\
                                                                {slot_grid[2][0]} {slot_grid[2][1]} {slot_grid[2][2]}", inline=False)
                    
                    await msg.edit(embed=embed)
                    await asyncio.sleep(SLOTS_ROTATE_DELAY)
                
                # Calculate the win or loss of the user based on the final grid of slot symbols. it is possible to win multiple times in one spin
                payout = 0
                # horizontal wins
                if slot_grid[0][0] == slot_grid[0][1] == slot_grid[0][2]:
                    payout += SLOT_SYMBOLS[slot_grid[0][0]] * bet
                if slot_grid[1][0] == slot_grid[1][1] == slot_grid[1][2]:
                    payout += SLOT_SYMBOLS[slot_grid[1][0]] * bet
                if slot_grid[2][0] == slot_grid[2][1] == slot_grid[2][2]:
                    payout += SLOT_SYMBOLS[slot_grid[2][0]] * bet
                #vertical wins
                if slot_grid[0][0] == slot_grid[1][0] == slot_grid[2][0]:
                    payout += SLOT_SYMBOLS[slot_grid[0][0]] * bet
                if slot_grid[0][1] == slot_grid[1][1] == slot_grid[2][1]:
                    payout += SLOT_SYMBOLS[slot_grid[0][1]] * bet
                if slot_grid[0][2] == slot_grid[1][2] == slot_grid[2][2]:
                    payout += SLOT_SYMBOLS[slot_grid[0][2]] * bet
                # 2 diagonal wins
                if slot_grid[0][0] == slot_grid[1][1] == slot_grid[2][2]:
                    payout += SLOT_SYMBOLS[slot_grid[0][0]] * (bet/2)
                if slot_grid[0][2] == slot_grid[1][1] == slot_grid[2][0]:
                    payout += SLOT_SYMBOLS[slot_grid[0][2]] * (bet/2)
                
                payout = round(payout, 2)
                if payout > 0:
                    new_balance = current_balance + payout
                    await cur.execute("UPDATE economy_data SET balance = ?, slots_wins = slots_wins + 1 WHERE user_id = ?", (new_balance, user_id))
                    slots_wins += 1
                    result_embed = discord.Embed(title="Slot Machine", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}\n\
                                                                                    {slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n\
                                                                                    {slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n\
                                                                                    {slot_grid[2][0]} {slot_grid[2][1]} {slot_grid[2][2]}\n\n\
                                                                                    You won {payout} {currency_singular if bet == 1 else currency_plural}!\
                                                                                    Your new balance is {current_balance + payout} {currency_singular if bet == 1 else currency_plural}.\n\
                                                                                    You have won {slots_wins} {'time' if slots_wins == 1 else 'times'} and lost {slots_losses} {'time' if slots_losses == 1 else 'times'}.", color=0x00ff00, timestamp=datetime.now(timezone.utc))
                else:
                    new_balance = current_balance - bet
                    await cur.execute("UPDATE economy_data SET balance = ?, slots_losses = slots_losses + 1 WHERE user_id = ?", (new_balance, user_id,))
                    slots_losses += 1
                    result_embed = discord.Embed(title="Slot Machine", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}\n\
                                                                                    {slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n\
                                                                                    {slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n\
                                                                                    {slot_grid[2][0]} {slot_grid[2][1]} {slot_grid[2][2]}\n\n\
                                                                                    You lost {bet} {currency_singular if bet == 1 else currency_plural}.\
                                                                                    Your new balance is {current_balance - bet} {currency_singular if current_balance - bet == 1 else currency_plural}.\n\
                                                                                    You have won {slots_wins} {'time' if slots_wins == 1 else 'times'} and lost {slots_losses} {'time' if slots_losses == 1 else 'times'}.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                
                result_embed.set_footer(text=botversion)
                await msg.edit(embed=result_embed)
            await con.commit()
    
    @commands.command(name="coinflip", aliases=["cf"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def coinflip(self, ctx, guess:str, bet:float=10):
        '''
        - Flips a coin and gives you a chance to double your bet.
        - Guess either `heads / head / h`, `tails / tail / t`.
        '''
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        
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
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance, cf_wins, cf_losses FROM economy_data WHERE user_id = ?", (user_id,))
                current_balance, cf_wins, cf_losses = await cur.fetchone()
                
                if current_balance < bet:
                    msg = await ctx.reply(f"You don't have enough {currency_plural} to play Coinflip with a bet of {bet} {currency_singular if bet == 1 else currency_plural}. Your current balance is only {current_balance} {currency_singular if current_balance == 1 else currency_plural}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                elif bet <= 0:
                    msg = await ctx.reply(f"You can't bet {bet} {currency_plural}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                
                outcome_possibilities = ["Heads", "Tails", "Edge"]
                outcome_weights = [0.49, 0.49, 0.02]
                coin = ''.join(random.choices(outcome_possibilities, outcome_weights)[0])
                
                embed = discord.Embed(title="Coinflip", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}\nGuess: {guessed_coin}", color=0x00ff00, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Flipping coin", value='', inline=False)
                embed.set_footer(text=botversion)
                msg = await ctx.reply(embed=embed)
                
                dot = "."
                for i in range(1, 4):
                    embed.set_field_at(0, name=f"Flipping coin{dot*i}", value="", inline=False)
                    await msg.edit(embed=embed)
                    await asyncio.sleep(0.2)
                
                # Calculate the win or loss of the user
                if guessed_coin == coin:
                    if guessed_coin == "Edge":
                        payout = bet * 10
                    else:
                        payout = bet * 2
                    payout = round(payout, 2)
                    cf_wins += 1
                    await cur.execute("UPDATE economy_data SET balance = balance + ?, cf_wins = cf_wins + 1 WHERE user_id = ?", (payout, user_id))
                    result_embed = discord.Embed(title="Coinflip", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}\n\
                                                                                Guess: {guessed_coin}\nResult: {coin}\n\nCongratulations! You won {payout} {currency_plural}!\n\
                                                                                Your new balance is {current_balance + payout} {currency_plural}.\n\
                                                                                You have won {cf_wins} {'time' if cf_wins == 1 else 'times'} and lost {cf_losses} {'time' if cf_losses == 1 else 'times'}.", color=0x00ff00, timestamp=datetime.now(timezone.utc))
                else:
                    cf_losses += 1
                    await cur.execute("UPDATE economy_data SET balance = balance - ?, cf_losses = cf_losses + 1 WHERE user_id = ?", (bet, user_id))
                    result_embed = discord.Embed(title="Coinflip", description=f"bet: {bet} {currency_singular if bet == 1 else currency_plural}\n\
                                                                                Guess: {guessed_coin}\nResult: {coin}\n\nSorry, you lost {bet} {currency_singular if bet == 1 else currency_plural}.\n\
                                                                                Your new balance is {current_balance - bet} {currency_singular if current_balance - bet == 1 else currency_plural}.\n\
                                                                                You have won {cf_wins} {'time' if cf_wins == 1 else 'times'} and lost {cf_losses} {'time' if cf_losses == 1 else 'times'}.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                result_embed.set_footer(text=botversion)
                await msg.edit(embed=result_embed)
            await con.commit()
    
    @commands.command(name="blackjack", aliases=["bj"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def blackjack(self, ctx, bet:int=10):
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        user_id = ctx.author.id
        
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance, bj_wins, bj_losses, bj_ties FROM economy_data WHERE user_id = ?", (user_id,))
                current_balance, bj_wins, bj_losses, bj_ties = await cur.fetchone()
                
                if current_balance < bet:
                    msg = await ctx.reply(f"You don't have enough {currency_plural} to play Blackjack with a bet of {bet} {currency_singular if bet == 1 else currency_plural}. Your current balance is only {current_balance} {currency_singular if current_balance == 1 else currency_plural}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                elif bet <= 0:
                    msg = await ctx.reply(f"You can't bet {bet} {currency_plural}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                
                # Create a deck and shuffle it
                deck = [(rank, suit) for rank in CARD_RANKS for suit in CARD_SUITS]
                random.shuffle(deck)
                
                # Deal initial cards
                player_hand = [deck.pop(), deck.pop()]
                dealer_hand = [deck.pop(), deck.pop()]
                
                # Calculate initial values
                player_value = self.calculate_hand_value(player_hand)
                dealer_value = self.calculate_hand_value([dealer_hand[0]])  # Only show first dealer card initially
                
                # Create initial embed with card images
                embed, file = self.create_blackjack_embed(player_hand, dealer_hand, player_value, dealer_value, bet, True, current_balance)
                
                # Check for natural blackjack
                if player_value == 21 and len(player_hand) == 2:
                    full_dealer_value = self.calculate_hand_value(dealer_hand)
                    if full_dealer_value == 21 and len(dealer_hand) == 2:
                        # Both have blackjack - it's a push
                        embed, file = self.create_blackjack_embed(player_hand, dealer_hand, player_value, full_dealer_value, bet, False, current_balance)
                        embed.color = 0x0000FF  # Blue for push
                        embed.add_field(name="Result", value="Push! Both have Blackjack!", inline=False)
                        await cur.execute("UPDATE economy_data SET bj_ties = bj_ties + 1 WHERE user_id = ?", (user_id,))
                        bj_ties += 1
                        await ctx.reply(embed=embed, file=file)
                        await con.commit()
                        return
                    else:
                        # Player has natural blackjack - pays 3:2
                        payout = bet * 1.5
                        embed, file = self.create_blackjack_embed(player_hand, dealer_hand, player_value, full_dealer_value, bet, False, current_balance + payout)
                        embed.color = 0x00FF00  # Green for win
                        embed.add_field(name="Result", value=f"Blackjack! You win {payout} {currency_plural}!", inline=False)
                        await cur.execute("UPDATE economy_data SET balance = balance + ?, bj_wins = bj_wins + 1 WHERE user_id = ?", (payout, user_id,))
                        bj_wins += 1
                        await ctx.reply(embed=embed, file=file)
                        await con.commit()
                        return
                
                # Create the game view with buttons
                view = BlackjackView(ctx, self, deck, player_hand, dealer_hand, bet, current_balance, bj_wins, bj_losses, bj_ties)
                
                # Normal game flow
                msg = await ctx.reply(embed=embed, file=file, view=view)
                view.message = msg
            await con.commit()

    @commands.command(name="tictactoe", aliases=["ttt"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def tictactoe(self, ctx, playertwo: discord.Member, bet:int=10):
        """Play a game of Tic-Tac-Toe against another user with a bet."""
        # Check and initialize both players
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        await self.check_user(playertwo.id, playertwo.name, ctx.guild.id, functions.get_unix_time())
        
        # Don't allow playing against yourself
        if ctx.author.id == playertwo.id:
            await ctx.reply("You can't play against yourself!")
            return
        
        # Don't allow playing against bots
        if playertwo.bot:
            await ctx.reply("You can't play against a bot!")
            return
        
        # Check balances for both players
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance, ttt_wins, ttt_losses, ttt_ties FROM economy_data WHERE user_id = ?", (ctx.author.id,))
                player1_balance, p1_wins, p1_losses, p1_ties = await cur.fetchone()
                
                await cur.execute("SELECT balance, ttt_wins, ttt_losses, ttt_ties FROM economy_data WHERE user_id = ?", (playertwo.id,))
                player2_balance, p2_wins, p2_losses, p2_ties = await cur.fetchone()
                
                # Check if both players have enough currency
                if player1_balance < bet:
                    await ctx.reply(f"You don't have enough {currency_plural} to play Tic-Tac-Toe with a bet of {bet}.")
                    return
                
                if player2_balance < bet:
                    await ctx.reply(f"{playertwo.display_name} doesn't have enough {currency_plural} to play Tic-Tac-Toe with a bet of {bet}.")
                    return
                
                if bet <= 0:
                    await ctx.reply(f"You can't bet {bet} {currency_plural}.")
                    return
        
        # Create initial challenge message
        challenge_embed = discord.Embed(
            title="Tic-Tac-Toe Challenge",
            description=f"{playertwo.display_name}, {ctx.author.display_name} has challenged you to a game of Tic-Tac-Toe with a bet of {bet} {currency_plural}. Do you accept?",
            color=0xFFA500,  # Orange color
            timestamp=datetime.now(timezone.utc)
        )
        challenge_embed.set_footer(text=botversion)
        
        # Simple class for the accept/decline buttons
        class ChallengeView(discord.ui.View):
            def __init__(self, *, timeout=30):
                super().__init__(timeout=timeout)
                self.value = None
                
            async def on_timeout(self):
                # Change the message to show it timed out
                timeout_embed = discord.Embed(
                    title="Challenge Timed Out",
                    description=f"{playertwo.display_name} didn't respond in time.",
                    color=0xFF0000,
                    timestamp=datetime.now(timezone.utc)
                )
                timeout_embed.set_footer(text=botversion)
                await challenge_message.edit(embed=timeout_embed, view=None)
                
            @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
            async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != playertwo.id:
                    await interaction.response.send_message("You're not the challenged player!", ephemeral=True)
                    return
                    
                await interaction.response.defer()
                self.value = True
                self.stop()
                
            @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
            async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != playertwo.id:
                    await interaction.response.send_message("You're not the challenged player!", ephemeral=True)
                    return
                    
                # Update the embed to show declined
                decline_embed = discord.Embed(
                    title="Challenge Declined",
                    description=f"{playertwo.display_name} declined the Tic-Tac-Toe challenge.",
                    color=0xFF0000,
                    timestamp=datetime.now(timezone.utc)
                )
                decline_embed.set_footer(text=botversion)
                await interaction.response.edit_message(embed=decline_embed, view=None)
                
                self.value = False
                self.stop()
        
        # Send the challenge
        view = ChallengeView()
        challenge_message = await ctx.reply(embed=challenge_embed, view=view)
        
        # Wait for the player to respond
        await view.wait()
        
        # If they didn't accept or it timed out, we're done
        if not view.value:
            return
        
        # They accepted - START THE GAME DIRECTLY USING THE ORIGINAL MESSAGE
        # Create the game view but make player2 go first (invited player)
        view = TicTacToeView(ctx, playertwo, bet, p1_wins, p1_losses, p1_ties, p2_wins, p2_losses, p2_ties)
        
        # Set up the game board embed
        game_embed = discord.Embed(
            title="Tic-Tac-Toe",
            description=f"**{ctx.author.display_name}** (❌) vs **{playertwo.display_name}** (⭕)\n"
                        f"Bet: {bet} {currency_plural}\n\n"
                        f"Current turn: {playertwo.display_name} (⭕)",
            color=0x00FFFF,
            timestamp=datetime.now(timezone.utc)
        )
        game_embed.set_footer(text=botversion)
        
        # Update the challenge message with the game board
        await challenge_message.edit(embed=game_embed, view=view)
        view.message = challenge_message
    
    @commands.command(name="dicepoker", aliases=["dice"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def dicepoker(self, ctx, bet: int = 10):
        """
        Play Dice Poker - Roll 5 dice and get paid based on your hand.
        Payout table:
        - Five of a kind: 50x bet
        - Four of a kind: 10x bet
        - Full house: 7x bet
        - Straight: 5x bet
        - Three of a kind: 3x bet
        - Two pair: 2x bet
        - Pair: 1x bet (money back)
        """
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        user_id = ctx.author.id
        
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (user_id,))
                current_balance = await cur.fetchone()
                current_balance = current_balance[0] if current_balance else 0
                
                # Check if user has enough balance
                if current_balance < bet:
                    msg = await ctx.reply(f"You don't have enough {currency_plural} to play Dice Poker with a bet of {bet}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                elif bet <= 0:
                    msg = await ctx.reply(f"You can't bet {bet} {currency_plural}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                
                # Create initial embed
                embed = discord.Embed(
                    title="Dice Poker",
                    description=f"Bet: {bet} {currency_singular if bet == 1 else currency_plural}",
                    color=0x00ff00,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Rolling dice...", value="🎲 🎲 🎲 🎲 🎲", inline=False)
                embed.set_footer(text=botversion)
                msg = await ctx.reply(embed=embed)
                
                # Create initial dice image
                for _ in range(5):
                    await asyncio.sleep(0.4)
                    temp_dice = [random.randint(1, 6) for _ in range(5)]
                    temp_dice_display = " ".join([f"[{d}]" for d in temp_dice])
                    embed.set_field_at(0, name="Rolling dice...", value=temp_dice_display, inline=False)
                    await msg.edit(embed=embed)
                
                # Final roll
                await asyncio.sleep(0.5)
                dice = [random.randint(1, 6) for _ in range(5)]
                
                # # Create final dice image
                # dice_image = self.create_dice_image(dice)
                
                # # Convert the PIL image to a bytes object
                # with BytesIO() as image_binary:
                #     dice_image.save(image_binary, 'PNG')
                #     image_binary.seek(0)
                #     file = discord.File(fp=image_binary, filename="final_dice_roll.png")
                
                # # Update embed with final dice values
                # embed.set_field_at(0, name="Your dice", value=f"{' '.join([str(d) for d in dice])}", inline=False)
                # embed.set_image(url="attachment://final_dice_roll.png")
                # await msg.edit(embed=embed, attachments=[file])
                
                # Evaluate hand
                hand_type, multiplier = self.evaluate_dice_hand(dice)
                payout = bet * multiplier
                
                # Create the sorted dice image for the result
                sorted_dice = sorted(dice)
                sorted_dice_image = self.create_dice_image(sorted_dice, hand_type)
                
                with BytesIO() as image_binary:
                    sorted_dice_image.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    file = discord.File(fp=image_binary, filename="sorted_dice_roll.png")
                
                # Update database and create result embed
                if payout > 0:
                    new_balance = current_balance + payout - bet
                    await cur.execute("UPDATE economy_data SET balance = ? WHERE user_id = ?", 
                                    (new_balance, user_id))
                    
                    result_embed = discord.Embed(
                        title="Dice Poker - Winner!",
                        description=f"Bet: {bet} {currency_singular if bet == 1 else currency_plural}",
                        color=0x00ff00,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    result_embed.add_field(name="Your Hand", value=f"**{hand_type}**", inline=False)
                    result_embed.set_image(url="attachment://sorted_dice_roll.png")
                    result_embed.add_field(
                        name="Result", 
                        value=f"Payout: {payout} {currency_plural}\n"
                            f"Net win: {payout - bet} {currency_plural}", 
                        inline=False
                    )
                    result_embed.add_field(
                        name="Balance", 
                        value=f"{new_balance} {currency_plural}", 
                        inline=False
                    )
                else:
                    new_balance = current_balance - bet
                    await cur.execute("UPDATE economy_data SET balance = ? WHERE user_id = ?", 
                                    (new_balance, user_id))
                    
                    result_embed = discord.Embed(
                        title="Dice Poker - No win",
                        description=f"Bet: {bet} {currency_singular if bet == 1 else currency_plural}",
                        color=0xff0000,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    result_embed.add_field(name="Your Hand", value=f"**{hand_type}**", inline=False)
                    result_embed.set_image(url="attachment://sorted_dice_roll.png")
                    result_embed.add_field(
                        name="Result", 
                        value=f"Better luck next time!", 
                        inline=False
                    )
                    result_embed.add_field(
                        name="Balance", 
                        value=f"{new_balance} {currency_plural}", 
                        inline=False
                    )
                    
                result_embed.set_footer(text=botversion)
                await msg.edit(embed=result_embed, attachments=[file])
            await con.commit()

class TicTacToeView(discord.ui.View):
    def __init__(self, ctx, player2, bet, p1_wins, p1_losses, p1_ties, p2_wins, p2_losses, p2_ties):
        super().__init__(timeout=180)  # 3 minutes to play the game
        self.ctx = ctx
        self.player1 = ctx.author
        self.player2 = player2
        self.bet = bet
        self.current_player = self.player2
        self.board = [["⬜" for _ in range(3)] for _ in range(3)]
        self.message = None
        self.game_over = False
        
        # Stats
        self.p1_wins = p1_wins
        self.p1_losses = p1_losses
        self.p1_ties = p1_ties
        self.p2_wins = p2_wins
        self.p2_losses = p2_losses
        self.p2_ties = p2_ties
        
        # Add the button grid (3x3)
        for row in range(3):
            for col in range(3):
                self.add_item(TicTacToeButton(row, col))
    
    async def interaction_check(self, interaction):
        # Only the current player can make a move
        if interaction.user.id == self.current_player.id:
            return True
        await interaction.response.send_message("It's not your turn!", ephemeral=True)
        return False
    
    async def on_timeout(self):
        if not self.game_over:
            self.game_over = True
            self.clear_items()
            
            embed = discord.Embed(
                title="Tic-Tac-Toe - Game Over",
                description=f"Game timed out! Both players keep their {currency_plural}.",
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=botversion)
            await self.message.edit(embed=embed, view=self)
    
    def check_winner(self):
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != "⬜":
                return row[0]
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != "⬜":
                return self.board[0][col]
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != "⬜":
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != "⬜":
            return self.board[0][2]
        
        # Check if board is full (tie)
        if all(self.board[i][j] != "⬜" for i in range(3) for j in range(3)):
            return "Tie"
        
        return None
    
    async def update_board(self, row, col, symbol):
        self.board[row][col] = symbol
        
        # Check for a winner
        result = self.check_winner()
        
        if result:
            self.game_over = True
            self.clear_items()
            
            # Display the final board with disabled buttons
            for r in range(3):
                for c in range(3):
                    button = TicTacToeButton(r, c, disabled=True)
                    button.label = self.board[r][c]
                    self.add_item(button)
            
            # Handle game result and update database
            if result == "Tie":
                await self.handle_tie()
            elif result == "❌":  # Player 1 wins
                await self.handle_win(self.player1, self.player2)
            else:  # Player 2 wins
                await self.handle_win(self.player2, self.player1)
        else:
            # Switch turns
            self.current_player = self.player2 if self.current_player == self.player1 else self.player1
            symbol_turn = "⭕" if self.current_player == self.player2 else "❌"
            
            # Update the game display
            embed = discord.Embed(
                title="Tic-Tac-Toe",
                description=f"**{self.player1.display_name}** (❌) vs **{self.player2.display_name}** (⭕)\n"
                            f"Bet: {self.bet} {currency_plural}\n\n"
                            f"Current turn: {self.current_player.display_name} ({symbol_turn})",
                color=0x00FFFF,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=botversion)
            await self.message.edit(embed=embed, view=self)
    
    async def handle_win(self, winner, loser):
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                # Update winner stats & balance
                if winner.id == self.player1.id:
                    self.p1_wins += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance + ?, ttt_wins = ? WHERE user_id = ?",
                        (self.bet, self.p1_wins, winner.id)
                    )
                    
                    # Update loser stats & balance
                    self.p2_losses += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance - ?, ttt_losses = ? WHERE user_id = ?",
                        (self.bet, self.p2_losses, loser.id)
                    )
                else:
                    self.p2_wins += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance + ?, ttt_wins = ? WHERE user_id = ?",
                        (self.bet, self.p2_wins, winner.id)
                    )
                    
                    # Update loser stats & balance
                    self.p1_losses += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance - ?, ttt_losses = ? WHERE user_id = ?",
                        (self.bet, self.p1_losses, loser.id)
                    )
            await con.commit()
        
        # Create the win embed
        winner_symbol = "❌" if winner.id == self.player1.id else "⭕"
        embed = discord.Embed(
            title="Tic-Tac-Toe - Game Over",
            description=f"**{winner.display_name}** ({winner_symbol}) wins!\n\n"
                        f"**{winner.display_name}** wins {self.bet} {currency_plural} from **{loser.display_name}**\n\n"
                        f"Player 1 Stats: {self.p1_wins}W/{self.p1_losses}L/{self.p1_ties}T\n"
                        f"Player 2 Stats: {self.p2_wins}W/{self.p2_losses}L/{self.p2_ties}T",
            color=0x00FF00,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=botversion)
        await self.message.edit(embed=embed, view=self)
    
    async def handle_tie(self):
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                # Update tie stats (no balance changes)
                self.p1_ties += 1
                self.p2_ties += 1
                await cur.execute(
                    "UPDATE economy_data SET ttt_ties = ? WHERE user_id = ?",
                    (self.p1_ties, self.player1.id)
                )
                await cur.execute(
                    "UPDATE economy_data SET ttt_ties = ? WHERE user_id = ?",
                    (self.p2_ties, self.player2.id)
                )
            await con.commit()
        
        # Create the tie embed
        embed = discord.Embed(
            title="Tic-Tac-Toe - Game Over",
            description=f"It's a tie! Both players keep their {currency_plural}.\n\n"
                        f"Player 1 Stats: {self.p1_wins}W/{self.p1_losses}L/{self.p1_ties}T\n"
                        f"Player 2 Stats: {self.p2_wins}W/{self.p2_losses}L/{self.p2_ties}T",
            color=0x0000FF,  # Blue for tie
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=botversion)
        await self.message.edit(embed=embed, view=self)

class TicTacToeButton(discord.ui.Button):
    def __init__(self, row, col, disabled=False):
        super().__init__(style=discord.ButtonStyle.secondary, label="⬜", row=row, disabled=disabled)
        self.row_pos = row
        self.col_pos = col
    
    async def callback(self, interaction):
        view = self.view
        
        # Determine the current player's symbol
        symbol = "❌" if view.current_player == view.player1 else "⭕"
        
        # Update the button appearance
        self.style = discord.ButtonStyle.danger if symbol == "❌" else discord.ButtonStyle.success
        self.label = symbol
        self.disabled = True
        
        # Update the game state
        await interaction.response.defer()
        await view.update_board(self.row_pos, self.col_pos, symbol)

class TicTacToeConfirmView(discord.ui.View):
    def __init__(self, ctx, player2, bet):
        super().__init__(timeout=30)  # Increase timeout to 30 seconds
        self.ctx = ctx
        self.player2 = player2
        self.bet = bet
        self.message = None
        self.accepted = False
        self.declined_message_sent = False
    
    async def interaction_check(self, interaction):
        # Only player 2 can interact with this view
        if interaction.user.id == self.player2.id:
            return True
        await interaction.response.send_message("You're not the challenged player!", ephemeral=True)
        return False
    
    async def on_timeout(self):
        if self.message:
            self.clear_items()
            embed = discord.Embed(
                title="Challenge Timed Out",
                description=f"{self.player2.display_name} didn't respond in time.",
                color=0xFF0000
            )
            await self.message.edit(embed=embed, view=self)
    
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept_button(self, interaction):
        self.accepted = True
        
        # Simply defer - no message editing here!
        # This prevents racing with the main command flow
        await interaction.response.defer()
        
        # Stop the view to continue the main command flow
        self.stop()
    
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction):
        self.accepted = False
        self.declined_message_sent = True
        
        # Update message here since we're declining
        await interaction.response.edit_message(
            content=f"{self.player2.display_name} declined the Tic-Tac-Toe challenge.",
            view=None
        )
        
        # Stop the view
        self.stop()

class BlackjackView(View):
    def __init__(self, ctx, cog, deck, player_hand, dealer_hand, bet, balance, wins, losses, ties):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.cog = cog
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.bet = bet
        self.balance = balance
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.message = None
        self.doubled_down = False
    
    async def interaction_check(self, interaction):
        if interaction.user.id == self.ctx.author.id:
            return True
        await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
        return False
    
    async def on_timeout(self):
        """Auto-stand when the buttons timeout"""
        if self.message:
            self.clear_items()
            await self.message.edit(view=self)
            await self.stand_action()
    
    async def end_game(self, result, payout=0, is_push=False):
        self.clear_items()  # Remove all buttons
        self.stop()  # Stop the view to prevent timeout
        
        async with aiosqlite.connect(economy_data) as con:
            async with con.cursor() as cur:
                if is_push:
                    await cur.execute(
                        "UPDATE economy_data SET bj_ties = bj_ties + 1 WHERE user_id = ?",
                        (self.ctx.author.id,)
                    )
                    self.ties += 1
                elif payout > 0:
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance + ?, bj_wins = bj_wins + 1 WHERE user_id = ?",
                        (payout, self.ctx.author.id)
                    )
                    self.wins += 1
                    self.balance += payout
                else:
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance - ?, bj_losses = bj_losses + 1 WHERE user_id = ?",
                        (self.bet, self.ctx.author.id)
                    )
                    self.losses += 1
                    self.balance -= self.bet
            await con.commit()
        
        # Calculate final values
        player_value = self.cog.calculate_hand_value(self.player_hand)
        dealer_value = self.cog.calculate_hand_value(self.dealer_hand)
        
        # Set embed color based on game outcome
        if is_push:
            # Blue for ties/push
            embed_color = 0x0000FF
        elif payout > 0:
            # Green for wins
            embed_color = 0x00FF00
        else:
            # Red for losses
            embed_color = 0xFF0000
        
        # Create updated embed for the final state
        embed = discord.Embed(
            title="Blackjack",
            description=f"Bet: {self.bet} {currency_singular if self.bet == 1 else currency_plural}",
            color=embed_color,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Format player's hand
        player_cards_str = [f"{card[0]} of {card[1]}" for card in self.player_hand]
        embed.add_field(
            name=f"Your Hand ({player_value})",
            value="\n".join(player_cards_str),
            inline=True
        )
        
        # Format dealer's hand (show all cards)
        dealer_cards_str = [f"{card[0]} of {card[1]}" for card in self.dealer_hand]
        embed.add_field(
            name=f"Dealer's Hand ({dealer_value})",
            value="\n".join(dealer_cards_str),
            inline=True
        )
        
        # Create card image showing all cards
        card_image = self.cog.create_hand_image(
            self.player_hand, 
            self.dealer_hand, 
            hide_dealer_card=False
        )
        
        # Convert the PIL image to a file
        with BytesIO() as image_binary:
            card_image.save(image_binary, 'PNG')
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename="blackjack_cards.png")
        
        embed.set_image(url="attachment://blackjack_cards.png")
        embed.add_field(name="Balance", value=f"{self.balance} {currency_plural}", inline=False)
        embed.add_field(
            name="Result", 
            value=f"{result}\nW: {self.wins} L: {self.losses} T: {self.ties}", 
            inline=False
        )
        embed.set_footer(text=botversion)
        
        # Update message with final state
        await self.message.edit(embed=embed, attachments=[file], view=self)
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction, button):
        # await interaction.response.defer()
        await interaction.response.edit_message(view=self)
        await self.hit_action()
    
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand_button(self, interaction, button):
        # await interaction.response.defer()
        await interaction.response.edit_message(view=self)
        await self.stand_action()
    
    @discord.ui.button(label="Double Down", style=discord.ButtonStyle.success)
    async def double_down_button(self, interaction, button):
        # Can only double down on first two cards
        if len(self.player_hand) != 2:
            await interaction.response.send_message("You can only double down on your first turn!", ephemeral=True)
            return
        
        if self.balance < self.bet * 2:
            await interaction.response.send_message(f"You need {self.bet * 2} {currency_plural} to double down!", ephemeral=True)
            return
            
        # await interaction.response.defer()
        await interaction.response.edit_message(view=self)
        self.doubled_down = True
        self.bet *= 2
        await self.hit_action(stand_after=True)
    
    async def hit_action(self, stand_after=False):
        print("Hit action triggered")
        # Deal a new card
        self.player_hand.append(self.deck.pop())
        player_value = self.cog.calculate_hand_value(self.player_hand)
        dealer_value = self.cog.calculate_hand_value([self.dealer_hand[0]])
        
        # Create updated embed with current state
        embed = discord.Embed(
            title="Blackjack",
            description=f"Bet: {self.bet} {currency_singular if self.bet == 1 else currency_plural}",
            color=0x00ff00,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Format player's hand
        player_cards_str = [f"{card[0]} of {card[1]}" for card in self.player_hand]
        embed.add_field(
            name=f"Your Hand ({player_value})",
            value="\n".join(player_cards_str),
            inline=True
        )
        
        # Format dealer's hand (hide second card)
        dealer_cards_str = [f"{self.dealer_hand[0][0]} of {self.dealer_hand[0][1]}", "?? of ??"]
        embed.add_field(
            name=f"Dealer's Hand ({dealer_value})",
            value="\n".join(dealer_cards_str),
            inline=True
        )
        
        # Create card image
        card_image = self.cog.create_hand_image(
            self.player_hand, 
            self.dealer_hand, 
            hide_dealer_card=True
        )
        
        # Convert the PIL image to a file
        with BytesIO() as image_binary:
            card_image.save(image_binary, 'PNG')
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename="blackjack_cards.png")
        
        embed.set_image(url="attachment://blackjack_cards.png")
        embed.add_field(name="Balance", value=f"{self.balance} {currency_plural}", inline=False)
        embed.set_footer(text=botversion)
        
        # Update the message with the new embed and attachment
        await self.message.edit(embed=embed, attachments=[file])
        
        # Check if player busted
        if player_value > 21:
            await self.end_game("Bust! You lose.")
            return
        
        # If player hit on double down, automatically stand
        if stand_after:
            await self.stand_action()
            return
    
    async def stand_action(self):
        print("Stand action triggered")
        # Dealer plays their hand
        self.dealer_hand, dealer_value = self.cog.dealer_play(self.deck, self.dealer_hand)
        player_value = self.cog.calculate_hand_value(self.player_hand)
        
        # Determine winner
        if dealer_value > 21:
            # Dealer busts
            payout = self.bet
            await self.end_game(f"Dealer busts! You win {payout} {currency_plural}!", payout)
        elif player_value > dealer_value:
            # Player wins
            payout = self.bet
            await self.end_game(f"You win {payout} {currency_plural}!", payout)
        elif player_value < dealer_value:
            # Dealer wins
            await self.end_game("Dealer wins, you lose.")
        else:
            # Push
            await self.end_game("Push! Your bet is returned.", self.bet, is_push=True)

async def setup(bot):
    await bot.add_cog(Economy(bot))