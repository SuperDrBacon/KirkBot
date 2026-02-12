import random
from datetime import datetime, timezone
from io import BytesIO

import aiosqlite
import discord
from discord.ui import View
from PIL import Image, ImageDraw, ImageFont

from cogs.utils.constants import (BOTVERSION, CARD_RANKS, CARD_SUITS,
                                  CARD_VALUES, CARDS, CURRENCY_PLURAL,
                                  CURRENCY_SINGULAR, ECONOMY_DATABASE,
                                  MSG_DEL_DELAY)


class BlackjackView(View):
    def __init__(self, ctx, deck, player_hand, dealer_hand, bet, balance, wins, losses, ties):
        super().__init__(timeout=60)
        self.ctx = ctx
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
        
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
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
        player_value = calculate_hand_value(self.player_hand)
        dealer_value = calculate_hand_value(self.dealer_hand)
        
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
            description=f"Bet: {self.bet} {CURRENCY_SINGULAR if self.bet == 1 else CURRENCY_PLURAL}",
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
        card_image = create_hand_image(
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
        embed.add_field(name="Balance", value=f"{self.balance} {CURRENCY_PLURAL}", inline=False)
        embed.add_field(
            name="Result", 
            value=f"{result}\nW: {self.wins} L: {self.losses} T: {self.ties}", 
            inline=False
        )
        embed.set_footer(text=BOTVERSION)
        
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
            await interaction.response.send_message(f"You need {self.bet * 2} {CURRENCY_PLURAL} to double down!", ephemeral=True)
            return
            
        # await interaction.response.defer()
        await interaction.response.edit_message(view=self)
        self.doubled_down = True
        self.bet *= 2
        await self.hit_action(stand_after=True)
    
    async def hit_action(self, stand_after=False):
        # Deal a new card
        self.player_hand.append(self.deck.pop())
        player_value = calculate_hand_value(self.player_hand)
        dealer_value = calculate_hand_value([self.dealer_hand[0]])
        
        # Disable the double down button after first hit
        if len(self.player_hand) > 2:
            # Find the double down button and disable it
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label == "Double Down":
                    item.disabled = True
                    break
        
        # Create updated embed with current state
        embed = discord.Embed(
            title="Blackjack",
            description=f"Bet: {self.bet} {CURRENCY_SINGULAR if self.bet == 1 else CURRENCY_PLURAL}",
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
        card_image = create_hand_image(
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
        embed.add_field(name="Balance", value=f"{self.balance} {CURRENCY_PLURAL}", inline=False)
        embed.set_footer(text=BOTVERSION)
        
        # Update the message with the new embed and attachment
        await self.message.edit(embed=embed, attachments=[file], view=self)
        
        # Check if player busted
        if player_value > 21:
            await self.end_game("Bust! You lose.")
            return
        
        # If player hit on double down, automatically stand
        if stand_after:
            await self.stand_action()
            return
    
    async def stand_action(self):
        # Dealer plays their hand
        dealer_hand, dealer_value = dealer_play(self.deck, self.dealer_hand)
        player_value = calculate_hand_value(self.player_hand)
        
        # Determine winner
        if dealer_value > 21:
            # Dealer busts
            payout = self.bet
            await self.end_game(f"Dealer busts! You win {payout} {CURRENCY_PLURAL}!", payout)
        elif player_value > dealer_value:
            # Player wins
            payout = self.bet
            await self.end_game(f"You win {payout} {CURRENCY_PLURAL}!", payout)
        elif player_value < dealer_value:
            # Dealer wins
            await self.end_game("Dealer wins, you lose.")
        else:
            # Push
            await self.end_game("Push! Your bet is returned.", self.bet, is_push=True)

def calculate_hand_value(hand):
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

def create_blackjack_embed(player_hand, dealer_hand, player_value, dealer_value, bet, hide_dealer_card=True, balance=0):
    """Create a beautiful embed for the blackjack game with card images."""
    embed = discord.Embed(
        title="Blackjack",
        description=f"Bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}",
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
    card_image = create_hand_image(player_hand, dealer_hand, hide_dealer_card)
    
    # Convert the PIL image to a bytes object
    with BytesIO() as image_binary:
        card_image.save(image_binary, 'PNG')
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename="blackjack_cards.png")
        embed.set_image(url="attachment://blackjack_cards.png")
    
    embed.add_field(name="Balance", value=f"{balance} {CURRENCY_PLURAL}", inline=False)
    embed.set_footer(text=BOTVERSION)
    
    return embed, file

def dealer_play(deck, dealer_hand):
    """Dealer plays their hand according to standard rules."""
    dealer_value = calculate_hand_value(dealer_hand)
    
    # Dealer must hit on 16 or lower, stand on 17 or higher
    while dealer_value < 17:
        dealer_hand.append(deck.pop())
        dealer_value = calculate_hand_value(dealer_hand)
    
    return dealer_hand, dealer_value

def create_hand_image(player_hand, dealer_hand, hide_dealer_card=True):
        """Create a combined image of all cards in player's and dealer's hands."""
        # Set up image dimensions
        card_width = 100
        card_height = 145
        card_spacing = 10
        padding = 15
        label_height = 30        # Space reserved for each label
        section_gap = 20         # Gap between dealer and player sections
        divider_thickness = 2

        # Calculate total width needed
        max_cards = max(len(player_hand), len(dealer_hand))
        cards_width = (max_cards * card_width) + ((max_cards - 1) * card_spacing)
        total_width = cards_width + (2 * padding)

        # Layout: padding + label + cards + section_gap + divider + section_gap + label + cards + padding
        total_height = (
            padding
            + label_height + card_height        # Dealer section
            + section_gap + divider_thickness + section_gap
            + label_height + card_height        # Player section
            + padding
        )

        # Card-table green background
        bg_color = (30, 71, 36, 255)
        combined_image = Image.new('RGBA', (total_width, total_height), bg_color)
        draw = ImageDraw.Draw(combined_image)

        # Load fonts
        try:
            label_font = ImageFont.truetype("impact.ttf", 20)
        except IOError:
            label_font = ImageFont.load_default()

        # --- Y positions ---
        dealer_label_y = padding
        dealer_cards_y = padding + label_height
        divider_y = dealer_cards_y + card_height + section_gap
        player_label_y = divider_y + divider_thickness + section_gap
        player_cards_y = player_label_y + label_height

        # --- Draw labels with subtle background pill ---
        def draw_label(text, y):
            bbox = label_font.getbbox(text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            pill_x = padding
            pill_y = y
            pill_w = text_w + 16
            pill_h = text_h + 8
            draw.rounded_rectangle(
                [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
                radius=6,
                fill=(0, 0, 0, 120)
            )
            # Center text within the pill (account for bbox top offset)
            text_x = pill_x + (pill_w - text_w) // 2 - bbox[0]
            text_y = pill_y + (pill_h - text_h) // 2 - bbox[1]
            draw.text((text_x, text_y), text, fill=(255, 255, 255), font=label_font)

        draw_label("DEALER", dealer_label_y)
        draw_label("PLAYER", player_label_y)

        # --- Draw divider line ---
        draw.line(
            [(padding, divider_y), (total_width - padding, divider_y)],
            fill=(255, 255, 255, 100),
            width=divider_thickness
        )

        # --- Paste dealer cards ---
        x_offset = padding
        for i, card in enumerate(dealer_hand):
            if i > 0 and hide_dealer_card:
                card_key = 'card_back'
            else:
                rank, suit = card
                card_key = get_card_key(rank, suit)

            if card_key in CARDS:
                card_path = CARDS[card_key][4]
                try:
                    card_image = Image.open(card_path).convert('RGBA')
                    card_image = card_image.resize((card_width, card_height))
                    combined_image.paste(card_image, (x_offset, dealer_cards_y), card_image)
                    x_offset += card_width + card_spacing
                except Exception as e:
                    print(f"Error loading card image: {e}")

        # --- Paste player cards ---
        x_offset = padding
        for card in player_hand:
            rank, suit = card
            card_key = get_card_key(rank, suit)

            if card_key in CARDS:
                card_path = CARDS[card_key][4]
                try:
                    card_image = Image.open(card_path).convert('RGBA')
                    card_image = card_image.resize((card_width, card_height))
                    combined_image.paste(card_image, (x_offset, player_cards_y), card_image)
                    x_offset += card_width + card_spacing
                except Exception as e:
                    print(f"Error loading card image: {e}")

        return combined_image

def get_card_key(rank, suit):
    rank_lower = rank.lower()
    suit_lower = suit.lower()
    # The CARDS dictionary keys are in the format suit_rank
    return f"{suit_lower}_{rank_lower}"

# Command handler that would be called from the Economy cog
async def blackjack_command(self, ctx, bet=10):
    user_id = ctx.author.id
    
    async with aiosqlite.connect(ECONOMY_DATABASE) as con:
        async with con.cursor() as cur:
            await cur.execute("SELECT balance, bj_wins, bj_losses, bj_ties FROM economy_data WHERE user_id = ?", (user_id,))
            current_balance, bj_wins, bj_losses, bj_ties = await cur.fetchone()
            
            if current_balance < bet:
                msg = await ctx.reply(f"You don't have enough {CURRENCY_PLURAL} to play Blackjack with a bet of {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}. Your current balance is only {current_balance} {CURRENCY_SINGULAR if current_balance == 1 else CURRENCY_PLURAL}.")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await msg.delete(delay=MSG_DEL_DELAY)
                return
            elif bet <= 0:
                msg = await ctx.reply(f"You can't bet {bet} {CURRENCY_PLURAL}.")
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
            player_value = calculate_hand_value(player_hand)
            dealer_value = calculate_hand_value([dealer_hand[0]])  # Only show first dealer card initially
            
            # Create initial embed with card images
            embed, file = create_blackjack_embed(player_hand, dealer_hand, player_value, dealer_value, bet, True, current_balance)
            
            # Check for natural blackjack
            if player_value == 21 and len(player_hand) == 2:
                full_dealer_value = calculate_hand_value(dealer_hand)
                if full_dealer_value == 21 and len(dealer_hand) == 2:
                    # Both have blackjack - it's a push
                    embed, file = create_blackjack_embed(player_hand, dealer_hand, player_value, full_dealer_value, bet, False, current_balance)
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
                    embed, file = create_blackjack_embed(player_hand, dealer_hand, player_value, full_dealer_value, bet, False, current_balance + payout)
                    embed.color = 0x00FF00  # Green for win
                    embed.add_field(name="Result", value=f"Blackjack! You win {payout} {CURRENCY_PLURAL}!", inline=False)
                    await cur.execute("UPDATE economy_data SET balance = balance + ?, bj_wins = bj_wins + 1 WHERE user_id = ?", (payout, user_id,))
                    bj_wins += 1
                    await ctx.reply(embed=embed, file=file)
                    await con.commit()
                    return
            
            # Create the game view with buttons
            view = BlackjackView(ctx, deck, player_hand, dealer_hand, bet, current_balance, bj_wins, bj_losses, bj_ties)
            
            # Normal game flow
            msg = await ctx.reply(embed=embed, file=file, view=view)
            view.message = msg
        await con.commit()