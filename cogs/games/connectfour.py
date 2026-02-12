import asyncio
import random
from datetime import datetime, timezone

import aiosqlite
import discord

from cogs.utils.constants import (BOTVERSION, COMMAND_PREFIX, CURRENCY_PLURAL,
                                  CURRENCY_SINGULAR, ECONOMY_DATABASE)


class ConnectFourView(discord.ui.View):
    def __init__(self, ctx, player2, bet, p1_wins, p1_losses, p1_ties, p2_wins, p2_losses, p2_ties):
        super().__init__(timeout=300)  # 5 minutes to play the game
        self.ctx = ctx
        self.player1 = ctx.author
        self.player2 = player2
        self.bet = bet
        self.current_player = self.player1 if player2.bot else self.player2
        self.rows = 6
        self.cols = 7
        self.board = [["⚪" for _ in range(self.cols)] for _ in range(self.rows)]
        self.message = None
        self.game_over = False
        self.bot = ctx.bot
        self.winning_positions = []  # Initialize winning positions list
        
        # Stats
        self.p1_wins = p1_wins
        self.p1_losses = p1_losses
        self.p1_ties = p1_ties
        self.p2_wins = p2_wins
        self.p2_losses = p2_losses
        self.p2_ties = p2_ties
        
        # Add the column buttons
        for col in range(self.cols):
            self.add_item(ConnectFourButton(col))
    
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
                title="Connect Four - Game Over",
                description=f"Game timed out! Both players keep their {CURRENCY_PLURAL}.",
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=BOTVERSION)
            await self.message.edit(embed=embed, view=self)
    
    def get_board_display(self):
        """Convert the board to a string representation"""
        # Column numbers at the top
        board_str = ""
        bottom_str = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣\n"
        
        # Board contents with highlighted winning positions if available
        for r, row in enumerate(self.board):
            row_str = ""
            for c, cell in enumerate(row):
                # Check if this position is part of the winning line
                if hasattr(self, 'winning_positions') and (r, c) in self.winning_positions:
                    # Replace with green circle versions
                    if cell == "🔴":
                        row_str += "🟢"  # Green circle for winning red
                    elif cell == "🔵":
                        row_str += "🟢"  # Green circle for winning blue
                    else:
                        row_str += cell
                else:
                    row_str += cell
            board_str += row_str + "\n"
        
        board_str += bottom_str
        return board_str
    
    def is_valid_move(self, col):
        """Check if a piece can be dropped in the specified column"""
        return self.board[0][col] == "⚪"  # Check if the top cell is empty
    
    def drop_piece(self, col, piece):
        """Drop a piece in the specified column and return the row where it lands"""
        for row in range(self.rows-1, -1, -1):  # Start from bottom, go up
            if self.board[row][col] == "⚪":
                self.board[row][col] = piece
                return row
        return -1  # Should never happen if is_valid_move is called first
    
    def check_winner(self, row, col, piece):
        """Check if the player who just placed a piece has won"""
        directions = [
            [(0, 1), (0, -1)],     # horizontal
            [(1, 0), (-1, 0)],     # vertical
            [(1, 1), (-1, -1)],    # diagonal /
            [(1, -1), (-1, 1)]     # diagonal \
        ]
        
        # Track winning positions
        self.winning_positions = []
        
        for direction_pair in directions:
            count = 1  # Count the piece that was just placed
            positions = [(row, col)]  # Start with current position
            
            # Check in both directions
            for dx, dy in direction_pair:
                # Check up to 3 pieces in this direction
                for i in range(1, 4):
                    r, c = row + i*dx, col + i*dy
                    # Check bounds
                    if 0 <= r < self.rows and 0 <= c < self.cols and self.board[r][c] == piece:
                        count += 1
                        positions.append((r, c))
                    else:
                        break
                        
            # If we found 4 or more in a row, it's a win
            if count >= 4:
                self.winning_positions = positions[:4]  # Store exactly 4 positions
                return True
                
        return False
    
    def is_board_full(self):
        """Check if the board is full (tie)"""
        return all(self.board[0][col] != "⚪" for col in range(self.cols))
    
    async def update_board(self, col):
        # Get the current player's piece
        piece = "🔴" if self.current_player == self.player1 else "🔵"
        
        # Drop the piece and get the row where it landed
        row = self.drop_piece(col, piece)
        
        # Check for a winner
        if self.check_winner(row, col, piece):
            self.game_over = True
            self.clear_items()
            
            # Add disabled buttons
            for c in range(self.cols):
                # Put first 4 buttons in row 0, remaining 3 in row 1
                self.add_item(ConnectFourButton(c, disabled=True))
            
            # Handle win
            await self.handle_win(self.current_player, self.player2 if self.current_player == self.player1 else self.player1)
        
        # Check for a tie
        elif self.is_board_full():
            self.game_over = True
            self.clear_items()
            
            # Add disabled buttons
            for c in range(self.cols):
                self.add_item(ConnectFourButton(c, disabled=True))
            
            # Handle tie
            await self.handle_tie()
        
        else:
            # Switch players
            self.current_player = self.player2 if self.current_player == self.player1 else self.player1
            
            # Update the game display
            board_display = self.get_board_display()
            embed = discord.Embed(
                title="Connect Four",
                description=f"**{self.player1.display_name}** (🔴) vs **{self.player2.display_name}** (🔵)\n"
                            f"Bet: {self.bet} {CURRENCY_PLURAL}\n\n"
                            f"{board_display}\n"
                            f"Current turn: {self.current_player.display_name} ({'🔴' if self.current_player == self.player1 else '🔵'})",
                color=0x00FFFF,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=BOTVERSION)
            await self.message.edit(embed=embed, view=self)
            
            # If it's the AI's turn, make an AI move after a short delay
            if not self.game_over and hasattr(self, 'bot') and self.current_player.id == self.bot.user.id:
                # await asyncio.sleep(1.5)  # Add a delay to make it feel more natural
                await self.ai_move()
    
    async def handle_win(self, winner, loser):
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
            async with con.cursor() as cur:
                # Update winner stats & balance
                if winner.id == self.player1.id:
                    self.p1_wins += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance + ?, c4_wins = ? WHERE user_id = ?",
                        (self.bet, self.p1_wins, winner.id)
                    )
                    
                    # Update loser stats & balance
                    self.p2_losses += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance - ?, c4_losses = ? WHERE user_id = ?",
                        (self.bet, self.p2_losses, loser.id)
                    )
                else:
                    self.p2_wins += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance + ?, c4_wins = ? WHERE user_id = ?",
                        (self.bet, self.p2_wins, winner.id)
                    )
                    
                    # Update loser stats & balance
                    self.p1_losses += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance - ?, c4_losses = ? WHERE user_id = ?",
                        (self.bet, self.p1_losses, loser.id)
                    )
                # Fetch updated balances
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player1.id,))
                p1_balance = (await cur.fetchone())[0]
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player2.id,))
                p2_balance = (await cur.fetchone())[0]
            await con.commit()
        
        # Create the win embed
        board_display = self.get_board_display()
        winner_piece = "🔴" if winner.id == self.player1.id else "🔵"
        
        # Build description with conditional player2 stats
        description = (f"**{winner.display_name}** ({winner_piece}) wins!\n\n"
                        f"{board_display}\n"
                        f"**{winner.display_name}** wins {self.bet} {CURRENCY_PLURAL} from **{loser.display_name}**\n\n"
                        f"{self.player1.display_name}: {p1_balance} {CURRENCY_PLURAL} | {self.p1_wins}W/{self.p1_losses}L/{self.p1_ties}T")
        
        # Add player2 stats only for human opponents
        if not self.player2.bot:
            description += f"\n{self.player2.display_name}: {p2_balance} {CURRENCY_PLURAL} | {self.p2_wins}W/{self.p2_losses}L/{self.p2_ties}T"
        
        embed = discord.Embed(
            title="Connect Four - Game Over",
            description=description,
            color=0x00FF00,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=BOTVERSION)
        await self.message.edit(embed=embed, view=self)
    
    async def handle_tie(self):
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
            async with con.cursor() as cur:
                # Update tie stats (no balance changes)
                self.p1_ties += 1
                self.p2_ties += 1
                await cur.execute(
                    "UPDATE economy_data SET c4_ties = ? WHERE user_id = ?",
                    (self.p1_ties, self.player1.id)
                )
                await cur.execute(
                    "UPDATE economy_data SET c4_ties = ? WHERE user_id = ?",
                    (self.p2_ties, self.player2.id)
                )
                # Fetch updated balances
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player1.id,))
                p1_balance = (await cur.fetchone())[0]
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player2.id,))
                p2_balance = (await cur.fetchone())[0]
            await con.commit()
        
        # Create the tie embed
        board_display = self.get_board_display()
        
        # Build description with conditional player2 stats
        description = (f"It's a tie! Both players keep their {CURRENCY_PLURAL}.\n\n"
                        f"{board_display}\n\n"
                        f"{self.player1.display_name}: {p1_balance} {CURRENCY_PLURAL} | {self.p1_wins}W/{self.p1_losses}L/{self.p1_ties}T")
        
        # Add player2 stats only for human opponents
        if not self.player2.bot:
            description += f"\n{self.player2.display_name}: {p2_balance} {CURRENCY_PLURAL} | {self.p2_wins}W/{self.p2_losses}L/{self.p2_ties}T"
        
        embed = discord.Embed(
            title="Connect Four - Game Over",
            description=description,
            color=0x0000FF,  # Blue for tie
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=BOTVERSION)
        await self.message.edit(embed=embed, view=self)
    
    async def ai_move(self):
        """Make an AI move when playing against the bot"""
        if self.game_over or self.current_player.id != self.bot.user.id:
            return
        
        # AI strategy: Try to win if possible, block opponent if needed, or take best move
        
        # Check if AI can win in one move
        for col in range(self.cols):
            if not self.is_valid_move(col):
                continue
                
            # Simulate the move
            row = self.get_landing_row(col)
            self.board[row][col] = "🔵"  # AI piece
            
            # Check if this move wins
            if self.check_winner(row, col, "🔵"):
                # Undo simulation
                self.board[row][col] = "⚪"
                # Make the winning move
                await self.update_board(col)
                return
            
            # Undo simulation
            self.board[row][col] = "⚪"
        
        # Check if player could win in their next move and block
        for col in range(self.cols):
            if not self.is_valid_move(col):
                continue
                
            # Simulate the move
            row = self.get_landing_row(col)
            self.board[row][col] = "🔴"  # Player piece
            
            # Check if this move would let player win
            if self.check_winner(row, col, "🔴"):
                # Undo simulation
                self.board[row][col] = "⚪"
                # Block that move
                await self.update_board(col)
                return
            
            # Undo simulation
            self.board[row][col] = "⚪"
        
        # If no winning or blocking move, use strategy:
        # Prefer center column, avoid giving opponent winning moves
        col_priority = [3, 2, 4, 1, 5, 0, 6]  # Center first, then adjacent columns
        
        for col in col_priority:
            if self.is_valid_move(col):
                # Avoid moves that set up opponent to win
                row = self.get_landing_row(col)
                
                # Check if making this move would allow opponent to win in next move
                if row > 0:  # Only check if row above exists
                    # Simulate our move
                    self.board[row][col] = "🔵"
                    
                    # Check if opponent could win in the spot above our move
                    self.board[row-1][col] = "🔴"
                    if self.check_winner(row-1, col, "🔴"):
                        # This would set up opponent to win, avoid if possible
                        self.board[row-1][col] = "⚪"
                        self.board[row][col] = "⚪"
                        continue  # Try next column
                    
                    # Undo simulation
                    self.board[row-1][col] = "⚪"
                    self.board[row][col] = "⚪"
                
                # Make the move
                await self.update_board(col)
                return
        
        # If all strategies failed, make a random valid move
        valid_cols = [col for col in range(self.cols) if self.is_valid_move(col)]
        if valid_cols:
            await self.update_board(random.choice(valid_cols))
    
    def get_landing_row(self, col):
        """Get the row where a piece would land if dropped in this column"""
        for row in range(self.rows-1, -1, -1):  # Start from bottom, go up
            if self.board[row][col] == "⚪":
                return row
        return -1  # Should never happen if is_valid_move is called first

class ConnectFourButton(discord.ui.Button):
    def __init__(self, col, disabled=False):
        # Use column number + 1 for the label (1-7 instead of 0-6)
        # Put first 4 buttons (0-3) in row 0, remaining 3 buttons (4-6) in row 1
        row_num = 0 if col < 4 else 1
        super().__init__(style=discord.ButtonStyle.secondary, label=str(col+1), row=row_num, disabled=disabled)
        self.col = col
    
    async def callback(self, interaction):
        view = self.view
        
        # Check if the move is valid
        if not view.is_valid_move(self.col) or view.game_over:
            await interaction.response.send_message("That column is full! Try another one.", ephemeral=True)
            return
        
        # Defer the response
        await interaction.response.defer()
        
        # Update the game state
        await view.update_board(self.col)

class ChallengeView(discord.ui.View):
    '''
    A view for accepting or declining a Connect Four challenge.
    '''
    def __init__(self, challenger, challenged_user, *, timeout=30):
        super().__init__(timeout=timeout)
        self.value = None
        self.message = None
        self.challenger = challenger
        self.challenged_user = challenged_user
    
    async def interaction_check(self, interaction):
        # Only the challenged player can interact with this view
        if interaction.user.id == self.challenged_user.id:
            return True
        
        # Tell other users they can't interact with this
        await interaction.response.send_message(
            f"Only {self.challenged_user.display_name} can respond to this challenge.", 
            ephemeral=True
        )
        return False

    async def on_timeout(self):
        # Change the message to show it timed out
        if self.message:
            timeout_embed = discord.Embed(
                title="Challenge Timed Out",
                description="The challenge wasn't responded to in time.",
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc)
            )
            timeout_embed.set_footer(text=BOTVERSION)
            await self.message.edit(embed=timeout_embed, view=None)
    
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = True
        self.stop()
    
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update the embed to show declined
        decline_embed = discord.Embed(
            title="Challenge Declined",
            description="The Connect Four challenge was declined.",
            color=0xFF0000,
            timestamp=datetime.now(timezone.utc)
        )
        decline_embed.set_footer(text=BOTVERSION)
        await interaction.response.edit_message(embed=decline_embed, view=None)
        
        self.value = False
        self.stop()

async def connectfour_command(self, ctx, playertwo, bet):
    # Don't allow playing against yourself
    if playertwo and ctx.author.id == playertwo.id:
        await ctx.reply("You can't play against yourself!")
        return
    
    if bet <= 0:
        await ctx.reply(f"You can't bet {bet} {CURRENCY_PLURAL}.")
        return

    # Check if player2 is a bot
    if playertwo and playertwo.bot:
        await ctx.reply(f"If you want to play against the AI, just use `{COMMAND_PREFIX}connectfour` or `{COMMAND_PREFIX}c4` without mentioning a user.")
        return
    
    # Check user balance
    async with aiosqlite.connect(ECONOMY_DATABASE) as con:
        async with con.cursor() as cur:
            await cur.execute("SELECT balance, c4_wins, c4_losses, c4_ties FROM economy_data WHERE user_id = ?", (ctx.author.id,))
            player1_balance, p1_wins, p1_losses, p1_ties = await cur.fetchone()
            
            # Check if user has enough currency
            if player1_balance < bet:
                await ctx.reply(f"You don't have enough {CURRENCY_PLURAL} to play Connect Four with a bet of {bet}.")
                return
            
            if playertwo:
                # Check player 2 stats
                await cur.execute("SELECT balance, c4_wins, c4_losses, c4_ties FROM economy_data WHERE user_id = ?", (playertwo.id,))
                player2_balance, p2_wins, p2_losses, p2_ties = await cur.fetchone()
                
                if player2_balance < bet:
                    await ctx.reply(f"{playertwo.display_name} doesn't have enough {CURRENCY_PLURAL} to play Connect Four with a bet of {bet}.")
                    return
                
                # Create initial challenge message
                challenge_embed = discord.Embed(
                    title="Connect Four Challenge",
                    description=f"{playertwo.display_name}, {ctx.author.display_name} has challenged you to a game of Connect Four with a bet of {bet} {CURRENCY_PLURAL}. Do you accept?",
                    color=0xFFA500,  # Orange color
                    timestamp=datetime.now(timezone.utc)
                )
                challenge_embed.set_footer(text=BOTVERSION)
                
                # Create the challenge view
                view = ChallengeView(ctx.author, playertwo, timeout=30)
                challenge_message = await ctx.reply(embed=challenge_embed, view=view)
                view.message = challenge_message
                
                # Wait for the player to respond
                await view.wait()
                
                # If they didn't accept or it timed out, we're done
                if not view.value:
                    return
                
                # They accepted - create the game view
                game_view = ConnectFourView(ctx, playertwo, bet, p1_wins, p1_losses, p1_ties, p2_wins, p2_losses, p2_ties)
                
                # Set up the game board embed for human vs human
                board_display = game_view.get_board_display()
                game_embed = discord.Embed(
                    title="Connect Four",
                    description=f"**{ctx.author.display_name}** (🔴) vs **{playertwo.display_name}** (🔵)\n"
                                f"Bet: {bet} {CURRENCY_PLURAL}\n\n"
                                f"{board_display}\n"
                                f"Current turn: {playertwo.display_name} (🔵)",
                    color=0x00FFFF,
                    timestamp=datetime.now(timezone.utc)
                )
                game_embed.set_footer(text=BOTVERSION)
                
                # Update the challenge message with the game board
                await challenge_message.edit(embed=game_embed, view=game_view)
                game_view.message = challenge_message
            
            # Playing against AI
            else:
                ai_player = self.bot.user
                
                # Create game view with AI opponent
                game_view = ConnectFourView(ctx, ai_player, bet, p1_wins, p1_losses, p1_ties, 0, 0, 0)
                
                # Set up the game board embed for human vs AI
                board_display = game_view.get_board_display()
                game_embed = discord.Embed(
                    title="Connect Four vs. AI",
                    description=f"**{ctx.author.display_name}** (🔴) vs **{ai_player.display_name}** (🔵)\n"
                                f"Bet: {bet} {CURRENCY_PLURAL}\n\n"
                                f"{board_display}\n"
                                f"Current turn: {ctx.author.display_name} (🔴)",
                    color=0x00FFFF,
                    timestamp=datetime.now(timezone.utc)
                )
                game_embed.set_footer(text=BOTVERSION)
                
                # Send the game board
                challenge_message = await ctx.reply(embed=game_embed, view=game_view)
                game_view.message = challenge_message