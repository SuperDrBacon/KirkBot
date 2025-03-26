import aiosqlite
import discord
import cogs.utils.functions as functions

from datetime import datetime, timezone
from typing import Union
from discord.ext import commands

# Import game command handlers
from cogs.games.blackjack   import blackjack_command
from cogs.games.coinflip    import coinflip_command
from cogs.games.dicepoker   import dicepoker_command
from cogs.games.slots       import slots_command
from cogs.games.tictactoe   import tictactoe_command
from cogs.utils.constants import (
    BOTVERSION, CURRENCY_PLURAL, CURRENCY_SINGULAR, ECONOMY_DATABASE,
    MSG_DEL_DELAY, ONE_DAY, PERMISSIONS_DATABASE, STARTING_BALANCE, STARTING_BANK)


class Economy(commands.Cog):
    '''
    This module provides commands and functionality related to the economy system of the bot.
    '''
    def __init__(self, bot):
        self.bot = bot
        # asyncio.create_task(self.add_ttt_columns())  # Add new columns when cog loads
    
    # async def add_ttt_columns(self):
    #     async with aiosqlite.connect(ECONOMY_DATABASE) as con:
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
        
        async with aiosqlite.connect(PERMISSIONS_DATABASE) as con:
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
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
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
        
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
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
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (user_id,))
                result = await cur.fetchone()
        
        balance = result[0] if result else 0
        return balance
    
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
        
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (ctx.author.id,))
                result = await cur.fetchone()
        
        balance = result[0] if result else 0
        await ctx.reply(f"Your balance is {balance} {CURRENCY_SINGULAR if balance == 1 else CURRENCY_PLURAL}.")
    
    @commands.command(name="leaderboard", aliases=["lb"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def leaderboard(self, ctx):
        '''
        Make a list of the top 10 richest players.
        '''
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        
        # Query to get top 10 users with highest balance
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
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
                value=f"{balance} {CURRENCY_PLURAL}",
                inline=False
            )
        
        embed.set_footer(text=BOTVERSION)
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
        
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
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
                    msg = await ctx.reply(f"You have claimed your daily reward of 100 {CURRENCY_PLURAL}. Your new balance is {new_balance} {CURRENCY_PLURAL}.")
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
        
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
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
        
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
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
            embed.set_footer(text=BOTVERSION)
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
        await slots_command(ctx, bet)
    
    @commands.command(name="coinflip", aliases=["cf"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def coinflip(self, ctx, guess:str, bet:float=10):
        '''
        - Flips a coin and gives you a chance to double your bet.
        - Guess either `heads / head / h`, `tails / tail / t`.
        '''
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        await coinflip_command(ctx, guess, bet)
    
    @commands.command(name="blackjack", aliases=["bj"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def blackjack(self, ctx, bet:int=10):
        '''
        Play a game of blackjack against the bot.
        This command allows you to play the classic card game blackjack (21) with the bot as the dealer.
        You can bet your credits and try to win more by getting a better hand than the dealer.
        Parameters:
        -----------
        bet : int, optional
            The amount of credits you want to bet, default is 10.
        Rules:
        - Get closer to 21 than the dealer without going over
        - Face cards are worth 10, Aces are worth 1 or 11
        - If you get 21 with your first two cards (blackjack), you win 1.5x your bet
        - Dealer must hit until they have at least 17        
        '''
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        await blackjack_command(self, ctx, bet)

    @commands.command(name="tictactoe", aliases=["ttt"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def tictactoe(self, ctx, player_or_bet: Union[discord.Member, int]=None, bet:int=10):
        """Play a game of Tic-Tac-Toe against another user or the AI with a bet."""
        # Parse arguments - handle flexible command syntax
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        playertwo = None
        if isinstance(player_or_bet, discord.Member):
            playertwo = player_or_bet
            await self.check_user(playertwo.id, playertwo.name, ctx.guild.id, functions.get_unix_time())
        elif isinstance(player_or_bet, int):
            bet = player_or_bet
        await tictactoe_command(self, ctx, playertwo, bet)
    
    @commands.command(name="dicepoker", aliases=["dice"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @economy_commands_enabled()
    async def dicepoker(self, ctx, bet: int = 10):
        """
        Play Dice Poker - Roll 5 dice and get paid based on your hand.
        Payout table:
        - Five of a kind: 10x bet   was 50
        - Four of a kind: 5x bet    was 10
        - Full house: 4x bet        was 7
        - Straight: 3x bet          was 5
        - Three of a kind: 1.5x bet   was 3
        - Two pair: 0x bet        was 2
        - Pair: 1x bet 
        - No win: lose bet
        """
        await self.check_user(ctx.author.id, ctx.author.name, ctx.guild.id, functions.get_unix_time())
        await dicepoker_command(ctx, bet)



async def setup(bot):
    await bot.add_cog(Economy(bot))