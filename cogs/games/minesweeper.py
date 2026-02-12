import asyncio
import random
from datetime import datetime, timezone

import aiosqlite
import discord
from discord.ui import Button, View

from cogs.utils.constants import (BOTVERSION, COMMAND_PREFIX, CURRENCY_PLURAL,
                                  CURRENCY_SINGULAR, ECONOMY_DATABASE)


class MinesweeperGame:
    def __init__(self, difficulty):
        r"""Initialize a minesweeper game with the given difficulty.
        
        Difficulty levels:
        - 'easy': 5x5 grid with 4 mines (16% mine density)
        - 'medium': 5x5 grid with 6 mines (24% mine density)
        - 'hard': 5x5 grid with 8 mines (32% mine density)
        """
        self.difficulty = difficulty
        
        # All difficulties use a 5x5 grid
        self.rows = 5
        self.cols = 5
        
        # Set mine count based on difficulty
        if difficulty == 'easy':
            self.mines = 4
            self.multiplier = 2.0
        elif difficulty == 'medium':
            self.mines = 6
            self.multiplier = 3.0
        else:  # hard
            self.mines = 8
            self.multiplier = 5.0
        
        # Initialize the grid
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.revealed = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.flagged = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.first_move = True  # To ensure the first click is safe
        self.game_over = False
        self.won = False
    
    def place_mines(self, safe_row, safe_col):
        """Place mines randomly on the grid, ensuring the first clicked cell and its neighbors are safe."""
        # Identify all valid cells (excluding first click and its neighbors)
        valid_cells = []
        for r in range(self.rows):
            for c in range(self.cols):
                # Skip the safe cell and its neighbors
                if abs(r - safe_row) <= 1 and abs(c - safe_col) <= 1:
                    continue
                valid_cells.append((r, c))
        
        # Place mines randomly
        mine_cells = random.sample(valid_cells, min(self.mines, len(valid_cells)))
        for r, c in mine_cells:
            self.grid[r][c] = -1  # -1 represents a mine
        
        # Calculate numbers for cells adjacent to mines
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1:  # Skip if the cell itself is a mine
                    continue
                
                # Count nearby mines
                count = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] == -1:
                            count += 1
                
                self.grid[r][c] = count
    
    def reveal(self, row, col):
        """Reveal a cell. Returns True if the move was successful, False if it hit a mine."""
        # Handle first move
        if self.first_move:
            self.place_mines(row, col)
            self.first_move = False
        
        # Check if already revealed or flagged
        if self.revealed[row][col] or self.flagged[row][col]:
            return True
        
        # Reveal the cell
        self.revealed[row][col] = True
        
        # Check if it's a mine
        if self.grid[row][col] == -1:
            return False  # Game over
        
        # If it's a zero, reveal neighbors automatically
        if self.grid[row][col] == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols and not self.revealed[nr][nc]:
                        self.reveal(nr, nc)
        
        # Check if player has won
        self.check_win()
        return True
    
    def check_win(self):
        """Check if the player has won by revealing all non-mine cells."""
        for r in range(self.rows):
            for c in range(self.cols):
                # If there's a non-mine cell that's not revealed, game continues
                if self.grid[r][c] != -1 and not self.revealed[r][c]:
                    return False
        
        # All non-mine cells revealed, player wins!
        self.won = True
        self.game_over = True
        return True
    
    def reveal_all(self):
        """Reveal all cells (called when game is over)."""
        for r in range(self.rows):
            for c in range(self.cols):
                self.revealed[r][c] = True

class MinesweeperButton(discord.ui.Button):
    def __init__(self, row, col, style=discord.ButtonStyle.secondary, disabled=False):
        # Since we're using a 5x5 grid, button position is straightforward
        super().__init__(style=style, label="‎", row=row, disabled=disabled)
        self.row_pos = row
        self.col_pos = col
    
    async def callback(self, interaction):
        view = self.view
        
        # Only the game owner can interact
        if interaction.user.id != view.player.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        # Can't interact if game is over
        if view.game.game_over:
            await interaction.response.defer()
            return
        
        # Process the move
        row, col = self.row_pos, self.col_pos
        
        # Make the move
        safe = view.game.reveal(row, col)
        
        if not safe:
            # Hit a mine
            view.game.game_over = True
            await interaction.response.defer()
            await view.end_game(False)
            return
        
        # Check for win
        if view.game.won:
            await interaction.response.defer()
            await view.end_game(True)
            return
        
        await interaction.response.defer()
        
        # Update the board
        await view.update_board()

class MinesweeperView(discord.ui.View):
    def __init__(self, ctx, player, bet, difficulty, ms_wins, ms_losses, database):
        super().__init__(timeout=300)  # 5 minutes to play
        self.ctx = ctx
        self.player = player
        self.bet = bet
        self.difficulty = difficulty
        self.ms_wins = ms_wins
        self.ms_losses = ms_losses
        self.database = database
        self.message = None
        
        # Create the game
        self.game = MinesweeperGame(difficulty)
        
        # Add the minesweeper buttons
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                self.add_item(MinesweeperButton(r, c))
    
    async def interaction_check(self, interaction):
        # Only the player can interact with this view
        if interaction.user.id == self.player.id:
            return True
        await interaction.response.send_message("This isn't your game!", ephemeral=True)
        return False
    
    async def on_timeout(self):
        """Handle game timeout."""
        if not self.game.game_over:
            self.game.game_over = True
            await self.end_game(False, timeout=True)
    
    async def update_board(self):
        """Update the board display with current game state."""
        for child in self.children:
            if isinstance(child, MinesweeperButton):
                r, c = child.row_pos, child.col_pos
                
                if self.game.revealed[r][c]:
                    # Cell is revealed
                    if self.game.grid[r][c] == -1:
                        # It's a mine
                        child.style = discord.ButtonStyle.danger
                        child.label = "💣"
                    else:
                        # It's a number
                        child.style = discord.ButtonStyle.secondary
                        value = self.game.grid[r][c]
                        if value == 0:
                            child.label = "‎"  
                        else:
                            child.label = str(value)
                    child.disabled = True
                else:
                    # Cell is hidden
                    child.style = discord.ButtonStyle.secondary
                    child.label = "‎"  
                    
        # Create the embed with game info
        embed = self.create_game_embed()
        
        # Update the message
        await self.message.edit(embed=embed, view=self)
    
    def create_game_embed(self):
        """Create the embed for the game state."""
        # Count revealed and total cells
        total_cells = self.game.rows * self.game.cols
        revealed_cells = sum(row.count(True) for row in self.game.revealed)
        remaining_cells = total_cells - revealed_cells - self.game.mines
        
        # Calculate potential winnings
        potential_win = round(self.bet * self.game.multiplier, 2)
        
        embed = discord.Embed(
            title=f"Minesweeper - {self.difficulty.capitalize()}",
            description=f"**Bet:** {self.bet} {CURRENCY_PLURAL}\n"
                        f"**Potential Win:** {potential_win} {CURRENCY_PLURAL}\n"
                        f"**Mines:** {self.game.mines}\n"
                        f"**Remaining Cells:** {remaining_cells}",
            color=0x00FFFF,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_author(name=self.player.display_name, icon_url=self.player.display_avatar.url)
        embed.set_footer(text=BOTVERSION)
        
        return embed
    
    async def end_game(self, won, timeout=False):
        """End the game and update database."""
        self.game.game_over = True
        
        # Reveal all cells
        self.game.reveal_all()
        
        # Update the view to show all mines
        for child in self.children:
            if isinstance(child, MinesweeperButton):
                r, c = child.row_pos, child.col_pos
                
                if self.game.grid[r][c] == -1:
                    # It's a mine
                    child.style = discord.ButtonStyle.danger
                    child.label = "💣"
                else:
                    # It's a number
                    child.style = discord.ButtonStyle.secondary
                    value = self.game.grid[r][c]
                    if value == 0:
                        child.label = "‎"
                    else:
                        child.label = str(value)
                
                child.disabled = True
        
        # Update database and prepare result message
        async with aiosqlite.connect(self.database) as con:
            async with con.cursor() as cur:
                if won:
                    # Player won - give them winnings
                    winnings = round(self.bet * self.game.multiplier, 2)
                    self.ms_wins += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance + ?, ms_wins = ? WHERE user_id = ?",
                        (winnings, self.ms_wins, self.player.id)
                    )
                    result = f"You won {winnings} {CURRENCY_PLURAL}!"
                    color = 0x00FF00  # Green
                else:
                    # Player lost - deduct bet
                    self.ms_losses += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance - ?, ms_losses = ? WHERE user_id = ?",
                        (self.bet, self.ms_losses, self.player.id)
                    )
                    if timeout:
                        result = f"Game timed out! You lost your bet of {self.bet} {CURRENCY_PLURAL}."
                    else:
                        result = f"💥 BOOM! You hit a mine and lost your bet of {self.bet} {CURRENCY_PLURAL}."
                    color = 0xFF0000  # Red
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player.id,))
                new_balance = (await cur.fetchone())[0]
            await con.commit()
        
        # Create final embed
        embed = discord.Embed(
            title=f"Minesweeper - {self.difficulty.capitalize()} - Game Over",
            description=f"{result}\n\n"
                        f"Balance: {new_balance} {CURRENCY_PLURAL}\n"
                        f"Stats: {self.ms_wins}W/{self.ms_losses}L",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_author(name=self.player.display_name, icon_url=self.player.display_avatar.url)
        embed.set_footer(text=BOTVERSION)
        
        # Update the message
        await self.message.edit(embed=embed, view=self)
        self.stop()

async def minesweeper_command(self, ctx, difficulty=None, bet=10):
    """Play a game of Minesweeper with betting."""
    # If no difficulty specified, show selection screen
    if difficulty is None:
        view = DifficultySelectView(self, ctx, bet)
        embed = discord.Embed(
            title="Minesweeper - Choose Difficulty",
            description=f"Bet: {bet} {CURRENCY_PLURAL}\n\n"
                        f"🟢 **Easy** — 4 mines, 2x payout\n"
                        f"🟡 **Medium** — 6 mines, 3x payout\n"
                        f"🔴 **Hard** — 8 mines, 5x payout\n\n"
                        f"Tip: {COMMAND_PREFIX}minesweeper or {COMMAND_PREFIX}ms [difficulty] [bet] to skip this screen",
            color=0x00ff00,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=BOTVERSION)
        view.message = await ctx.reply(embed=embed, view=view)
        return

    # Validate difficulty
    if difficulty.lower() not in ['easy', 'medium', 'hard']:
        if difficulty.isdigit():
            # User likely provided bet first, adjust parameters
            bet = int(difficulty)
            difficulty = 'easy'
        else:
            await ctx.reply("Invalid difficulty! Choose 'easy', 'medium', or 'hard'.")
            return
    
    difficulty = difficulty.lower()
    
    # Check user balance
    async with aiosqlite.connect(ECONOMY_DATABASE) as con:
        async with con.cursor() as cur:
            # Get user's balance and stats
            await cur.execute("SELECT balance, ms_wins, ms_losses FROM economy_data WHERE user_id = ?", (ctx.author.id,))
            result = await cur.fetchone()
            
            if result:
                balance, ms_wins, ms_losses = result
                
                # Check if user has enough balance
                if balance < bet:
                    await ctx.reply(f"You don't have enough {CURRENCY_PLURAL} to play Minesweeper with a bet of {bet}.")
                    return
                elif bet <= 0:
                    await ctx.reply(f"You can't bet {bet} {CURRENCY_PLURAL}.")
                    return
            else:
                await ctx.reply("Failed to retrieve your balance. Please try again.")
                return
        
        # Create the game view
        view = MinesweeperView(ctx, ctx.author, bet, difficulty, ms_wins, ms_losses, ECONOMY_DATABASE)
        
        # Create initial embed
        embed = view.create_game_embed()
        
        # Send the message with the game board
        view.message = await ctx.reply(embed=embed, view=view)


class DifficultySelectView(discord.ui.View):
    """View that lets the user pick a minesweeper difficulty before starting."""
    def __init__(self, cog_self, ctx, bet):
        super().__init__(timeout=30)
        self.cog_self = cog_self
        self.ctx = ctx
        self.bet = bet
        self.message = None

    async def interaction_check(self, interaction):
        if interaction.user.id == self.ctx.author.id:
            return True
        await interaction.response.send_message("This isn't your game!", ephemeral=True)
        return False

    async def on_timeout(self):
        self.clear_items()
        if self.message:
            embed = discord.Embed(
                title="Minesweeper",
                description="Selection timed out.",
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=BOTVERSION)
            await self.message.edit(embed=embed, view=self)

    async def start_game(self, interaction, difficulty):
        self.stop()
        await self.message.delete()
        await minesweeper_command(self.cog_self, self.ctx, difficulty, self.bet)

    @discord.ui.button(label="Easy (2x)", style=discord.ButtonStyle.success)
    async def easy_button(self, interaction, button):
        await interaction.response.defer()
        await self.start_game(interaction, 'easy')

    @discord.ui.button(label="Medium (3x)", style=discord.ButtonStyle.primary)
    async def medium_button(self, interaction, button):
        await interaction.response.defer()
        await self.start_game(interaction, 'medium')

    @discord.ui.button(label="Hard (5x)", style=discord.ButtonStyle.danger)
    async def hard_button(self, interaction, button):
        await interaction.response.defer()
        await self.start_game(interaction, 'hard')