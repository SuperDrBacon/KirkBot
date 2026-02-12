import asyncio
import random
from datetime import datetime, timezone

import aiosqlite
import discord

from cogs.utils.constants import (BOTVERSION, COMMAND_PREFIX, CURRENCY_PLURAL,
                                  CURRENCY_SINGULAR, ECONOMY_DATABASE)


class TicTacToeAIView(discord.ui.View):
    def __init__(self, ctx, ai_player, bet, p1_wins, p1_losses, p1_ties):
        super().__init__(timeout=180)  # 3 minutes to play the game
        self.ctx = ctx
        self.player = ctx.author
        self.ai_player = ai_player
        self.bet = bet
        self.board = [["⬜" for _ in range(3)] for _ in range(3)]
        self.message = None
        self.game_over = False
        self.ai_symbol = "⭕"
        self.player_symbol = "❌"
        
        # Stats
        self.p1_wins = p1_wins
        self.p1_losses = p1_losses
        self.p1_ties = p1_ties
        
        # Add the button grid (3x3)
        for row in range(3):
            for col in range(3):
                self.add_item(TicTacToeAIButton(row, col))
    
    async def interaction_check(self, interaction):
        # Only the human player can make a move
        if interaction.user.id == self.player.id:
            return True
        await interaction.response.send_message("This isn't your game!", ephemeral=True)
        return False
    
    async def on_timeout(self):
        if not self.game_over:
            self.game_over = True
            self.clear_items()
            
            # Player loses the bet if they time out
            async with aiosqlite.connect(ECONOMY_DATABASE) as con:
                async with con.cursor() as cur:
                    self.p1_losses += 1
                    await cur.execute(
                        "UPDATE economy_data SET balance = balance - ?, ttt_losses = ? WHERE user_id = ?",
                        (self.bet, self.p1_losses, self.player.id)
                    )
                await con.commit()
            
            embed = discord.Embed(
                title="Tic-Tac-Toe - Game Over",
                description=f"Game timed out! You lose {self.bet} {CURRENCY_PLURAL}.",
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=BOTVERSION)
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
    
    def ai_make_move(self):
        """AI logic for making a move in Tic-Tac-Toe"""
        # Check if AI can win in one move
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == "⬜":
                    self.board[row][col] = self.ai_symbol
                    if self.check_winner() == self.ai_symbol:
                        self.board[row][col] = "⬜"  # Reset for now
                        return row, col
                    self.board[row][col] = "⬜"  # Undo the move
        
        # Check if player can win in one move and block
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == "⬜":
                    self.board[row][col] = self.player_symbol
                    if self.check_winner() == self.player_symbol:
                        self.board[row][col] = "⬜"  # Reset for now
                        return row, col
                    self.board[row][col] = "⬜"  # Undo the move
        
        # Try to take the center
        if self.board[1][1] == "⬜":
            return 1, 1
        
        # Try to take the corners
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        random.shuffle(corners)
        for row, col in corners:
            if self.board[row][col] == "⬜":
                return row, col
        
        # Take any available edge
        edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
        random.shuffle(edges)
        for row, col in edges:
            if self.board[row][col] == "⬜":
                return row, col
        
        # Shouldn't reach here if the board has empty spaces
        return None
    
    async def update_board(self, row, col, player_move=True):
        # Update board with player move
        if player_move:
            self.board[row][col] = self.player_symbol
        
        # Check for a winner after player's move
        result = self.check_winner()
        
        if result:
            await self.handle_game_end(result)
            return
        
        # AI's turn if game isn't over
        if player_move:
            await asyncio.sleep(1)  # Brief delay to make it seem like the AI is "thinking"
            
            ai_row, ai_col = self.ai_make_move()
            self.board[ai_row][ai_col] = self.ai_symbol
            
            # Update the button for AI's move
            for child in self.children:
                if isinstance(child, TicTacToeAIButton) and child.row_pos == ai_row and child.col_pos == ai_col:
                    child.style = discord.ButtonStyle.success
                    child.label = self.ai_symbol
                    child.disabled = True
                    break
            
            # Check for a winner after AI's move
            result = self.check_winner()
            
            if result:
                await self.handle_game_end(result)
                return
        
        # Update the game display
        embed = discord.Embed(
            title="Tic-Tac-Toe vs AI",
            description=f"**{self.player.display_name}** (❌) vs **{self.ai_player.name}** (⭕)\n"
                        f"Bet: {self.bet} {CURRENCY_PLURAL}\n\n"
                        f"Your turn! You are ❌",
            color=0x00FFFF,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=BOTVERSION)
        await self.message.edit(embed=embed, view=self)
    
    async def handle_game_end(self, result):
        self.game_over = True
        
        # Display the final board with disabled buttons
        for child in self.children:
            child.disabled = True
            if isinstance(child, TicTacToeAIButton):
                if child.label == self.player_symbol:
                    child.style = discord.ButtonStyle.danger
                elif child.label == self.ai_symbol:
                    child.style = discord.ButtonStyle.success
        
        # Handle game result and update database
        if result == "Tie":
            await self.handle_tie()
        elif result == self.player_symbol:  # Player wins
            await self.handle_player_win()
        else:  # AI wins
            await self.handle_ai_win()
    
    async def handle_player_win(self):
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
            async with con.cursor() as cur:
                # Update player stats & balance
                self.p1_wins += 1
                await cur.execute(
                    "UPDATE economy_data SET balance = balance + ?, ttt_wins = ? WHERE user_id = ?",
                    (self.bet, self.p1_wins, self.player.id)
                )
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player.id,))
                new_balance = (await cur.fetchone())[0]
            await con.commit()
        
        # Create the win embed
        embed = discord.Embed(
            title="Tic-Tac-Toe - Game Over",
            description=f"**{self.player.display_name}** (❌) wins!\n\n"
                        f"You win {self.bet} {CURRENCY_PLURAL}!\n\n"
                        f"Balance: {new_balance} {CURRENCY_PLURAL}\n"
                        f"Your Stats: {self.p1_wins}W/{self.p1_losses}L/{self.p1_ties}T",
            color=0x00FF00,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=BOTVERSION)
        await self.message.edit(embed=embed, view=self)
    
    async def handle_ai_win(self):
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
            async with con.cursor() as cur:
                # Update player stats & balance
                self.p1_losses += 1
                await cur.execute(
                    "UPDATE economy_data SET balance = balance - ?, ttt_losses = ? WHERE user_id = ?",
                    (self.bet, self.p1_losses, self.player.id)
                )
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player.id,))
                new_balance = (await cur.fetchone())[0]
            await con.commit()
        
        # Create the loss embed
        embed = discord.Embed(
            title="Tic-Tac-Toe - Game Over",
            description=f"**{self.ai_player.name}** (⭕) wins!\n\n"
                        f"You lose {self.bet} {CURRENCY_PLURAL}.\n\n"
                        f"Balance: {new_balance} {CURRENCY_PLURAL}\n"
                        f"Your Stats: {self.p1_wins}W/{self.p1_losses}L/{self.p1_ties}T",
            color=0xFF0000,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=BOTVERSION)
        await self.message.edit(embed=embed, view=self)
    
    async def handle_tie(self):
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
            async with con.cursor() as cur:
                # Update tie stats (no balance changes)
                self.p1_ties += 1
                await cur.execute(
                    "UPDATE economy_data SET ttt_ties = ? WHERE user_id = ?",
                    (self.p1_ties, self.player.id)
                )
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player.id,))
                new_balance = (await cur.fetchone())[0]
            await con.commit()
        
        # Create the tie embed
        embed = discord.Embed(
            title="Tic-Tac-Toe - Game Over",
            description=f"It's a tie! You keep your {CURRENCY_PLURAL}.\n\n"
                        f"Balance: {new_balance} {CURRENCY_PLURAL}\n"
                        f"Your Stats: {self.p1_wins}W/{self.p1_losses}L/{self.p1_ties}T",
            color=0x0000FF,  # Blue for tie
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=BOTVERSION)
        await self.message.edit(embed=embed, view=self)

class TicTacToeAIButton(discord.ui.Button):
    def __init__(self, row, col):
        super().__init__(style=discord.ButtonStyle.secondary, label="⬜", row=row)
        self.row_pos = row
        self.col_pos = col
    
    async def callback(self, interaction):
        view = self.view
        
        # Check if it's a valid move
        if view.board[self.row_pos][self.col_pos] != "⬜" or view.game_over:
            return
        
        # Update button appearance
        self.style = discord.ButtonStyle.danger
        self.label = view.player_symbol
        self.disabled = True
        
        # Defer the response to avoid interaction timeout
        await interaction.response.defer()
        
        # Update the game state
        await view.update_board(self.row_pos, self.col_pos)

class ChallengeView(discord.ui.View):
    '''
    A view for accepting or declining a Tic-Tac-Toe challenge.
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
            description="The Tic-Tac-Toe challenge was declined.",
            color=0xFF0000,
            timestamp=datetime.now(timezone.utc)
        )
        decline_embed.set_footer(text=BOTVERSION)
        await interaction.response.edit_message(embed=decline_embed, view=None)
        
        self.value = False
        self.stop()

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
                description=f"Game timed out! Both players keep their {CURRENCY_PLURAL}.",
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=BOTVERSION)
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
                            f"Bet: {self.bet} {CURRENCY_PLURAL}\n\n"
                            f"Current turn: {self.current_player.display_name} ({symbol_turn})",
                color=0x00FFFF,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=BOTVERSION)
            await self.message.edit(embed=embed, view=self)
    
    async def handle_win(self, winner, loser):
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
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
                # Fetch updated balances
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player1.id,))
                p1_balance = (await cur.fetchone())[0]
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player2.id,))
                p2_balance = (await cur.fetchone())[0]
            await con.commit()
        
        # Create the win embed
        winner_symbol = "❌" if winner.id == self.player1.id else "⭕"
        embed = discord.Embed(
            title="Tic-Tac-Toe - Game Over",
            description=f"**{winner.display_name}** ({winner_symbol}) wins!\n\n"
                        f"**{winner.display_name}** wins {self.bet} {CURRENCY_PLURAL} from **{loser.display_name}**\n\n"
                        f"{self.player1.display_name}: {p1_balance} {CURRENCY_PLURAL} | {self.p1_wins}W/{self.p1_losses}L/{self.p1_ties}T\n"
                        f"{self.player2.display_name}: {p2_balance} {CURRENCY_PLURAL} | {self.p2_wins}W/{self.p2_losses}L/{self.p2_ties}T",
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
                    "UPDATE economy_data SET ttt_ties = ? WHERE user_id = ?",
                    (self.p1_ties, self.player1.id)
                )
                await cur.execute(
                    "UPDATE economy_data SET ttt_ties = ? WHERE user_id = ?",
                    (self.p2_ties, self.player2.id)
                )
                # Fetch updated balances
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player1.id,))
                p1_balance = (await cur.fetchone())[0]
                await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (self.player2.id,))
                p2_balance = (await cur.fetchone())[0]
            await con.commit()
        
        # Create the tie embed
        embed = discord.Embed(
            title="Tic-Tac-Toe - Game Over",
            description=f"It's a tie! Both players keep their {CURRENCY_PLURAL}.\n\n"
                        f"{self.player1.display_name}: {p1_balance} {CURRENCY_PLURAL} | {self.p1_wins}W/{self.p1_losses}L/{self.p1_ties}T\n"
                        f"{self.player2.display_name}: {p2_balance} {CURRENCY_PLURAL} | {self.p2_wins}W/{self.p2_losses}L/{self.p2_ties}T",
            color=0x0000FF,  # Blue for tie
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=BOTVERSION)
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


async def tictactoe_command(self, ctx, playertwo, bet):
    # Don't allow playing against yourself
    if playertwo and ctx.author.id == playertwo.id:
        await ctx.reply("You can't play against yourself!")
        return
    
    if bet <= 0:
        await ctx.reply(f"You can't bet {bet} {CURRENCY_PLURAL}.")
        return
    
    # Check if player2 is a bot and not intentionally playing with AI
    if playertwo and playertwo.bot:
        await ctx.reply(f"If you want to play against the AI, just use `{COMMAND_PREFIX}tictactoe` or `{COMMAND_PREFIX}ttt` without mentioning a user.")
        return
    
    # Check user balance
    async with aiosqlite.connect(ECONOMY_DATABASE) as con:
        async with con.cursor() as cur:
            await cur.execute("SELECT balance, ttt_wins, ttt_losses, ttt_ties FROM economy_data WHERE user_id = ?", (ctx.author.id,))
            player1_balance, p1_wins, p1_losses, p1_ties = await cur.fetchone()
            
            # Check if user has enough currency
            if player1_balance < bet:
                await ctx.reply(f"You don't have enough {CURRENCY_PLURAL} to play Tic-Tac-Toe with a bet of {bet}.")
                return
            
            # If playing against another user
            if playertwo:
                # Check playertwo's balance
                await cur.execute("SELECT balance, ttt_wins, ttt_losses, ttt_ties FROM economy_data WHERE user_id = ?", (playertwo.id,))
                player2_balance, p2_wins, p2_losses, p2_ties = await cur.fetchone()
                
                if player2_balance < bet:
                    await ctx.reply(f"{playertwo.display_name} doesn't have enough {CURRENCY_PLURAL} to play Tic-Tac-Toe with a bet of {bet}.")
                    return
                
                # Create initial challenge message
                challenge_embed = discord.Embed(
                    title="Tic-Tac-Toe Challenge",
                    description=f"{playertwo.display_name}, {ctx.author.display_name} has challenged you to a game of Tic-Tac-Toe with a bet of {bet} {CURRENCY_PLURAL}. Do you accept?",
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
                game_view = TicTacToeView(ctx, playertwo, bet, p1_wins, p1_losses, p1_ties, p2_wins, p2_losses, p2_ties)
                
                # Set up the game board embed
                game_embed = discord.Embed(
                    title="Tic-Tac-Toe",
                    description=f"**{ctx.author.display_name}** (❌) vs **{playertwo.display_name}** (⭕)\n"
                                f"Bet: {bet} {CURRENCY_PLURAL}\n\n"
                                f"Current turn: {playertwo.display_name} (⭕)",
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
                game_view = TicTacToeAIView(ctx, ai_player, bet, p1_wins, p1_losses, p1_ties)
                
                # Set up the game board embed
                game_embed = discord.Embed(
                    title="Tic-Tac-Toe vs AI",
                    description=f"**{ctx.author.display_name}** (❌) vs **{self.bot.user.name}** (⭕)\n"
                                f"Bet: {bet} {CURRENCY_PLURAL}\n\n"
                                f"Your turn! You are ❌",
                    color=0x00FFFF,
                    timestamp=datetime.now(timezone.utc)
                )
                game_embed.set_footer(text=BOTVERSION)
                
                # Send the game board
                game_message = await ctx.reply(embed=game_embed, view=game_view)
                game_view.message = game_message