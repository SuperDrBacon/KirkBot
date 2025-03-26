import asyncio
import random
import discord
import aiosqlite

from io import BytesIO
from PIL import Image
from datetime import datetime, timezone
from cogs.utils.constants import BOTVERSION, CURRENCY_PLURAL, CURRENCY_SINGULAR, DICE, ECONOMY_DATABASE, MSG_DEL_DELAY


def evaluate_dice_hand(dice):
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
        return "Five of a Kind", 10
        
    # Check for four of a kind
    if values[0] == 4:
        return "Four of a Kind", 5
        
    # Check for full house (3 of a kind + pair)
    if values[0] == 3 and values[1] == 2:
        return "Full House", 4
        
    # Check for straight (5 consecutive values)
    if len(counts) == 5 and max(dice) - min(dice) == 4:
        return "Straight", 3
        
    # Check for three of a kind
    if values[0] == 3:
        return "Three of a Kind", 1.5
        
    # Check for two pair
    if values[0] == 2 and values[1] == 2:
        return "Two Pair", 1.2
        
    # Check for one pair
    if values[0] == 2:
        return "Pair", 0
        
    # High card - no win
    return "Nothing", 0

def create_dice_image(dice_values, hand_type="Nothing"):
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
        pass
        # Pair in green
        # for value, count in counts.items():
        #     if count == 2:
        #         for i, die in enumerate(dice_values):
        #             if die == value:
        #                 dice_colors[i] = 'green'
    
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

async def dicepoker_command(ctx, bet):
    user_id = ctx.author.id
    
    async with aiosqlite.connect(ECONOMY_DATABASE) as con:
        async with con.cursor() as cur:
            await cur.execute("SELECT balance FROM economy_data WHERE user_id = ?", (user_id,))
            current_balance = await cur.fetchone()
            current_balance = current_balance[0] if current_balance else 0
            
            # Check if user has enough balance
            if current_balance < bet:
                msg = await ctx.reply(f"You don't have enough {CURRENCY_PLURAL} to play Dice Poker with a bet of {bet}.")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await msg.delete(delay=MSG_DEL_DELAY)
                return
            elif bet <= 0:
                msg = await ctx.reply(f"You can't bet {bet} {CURRENCY_PLURAL}.")
                await ctx.message.delete(delay=MSG_DEL_DELAY)
                await msg.delete(delay=MSG_DEL_DELAY)
                return
            
            # Create initial embed
            embed = discord.Embed(
                title="Dice Poker",
                description=f"Bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Rolling dice...", value="🎲 🎲 🎲 🎲 🎲", inline=False)
            embed.set_footer(text=BOTVERSION)
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
            
            # Evaluate hand
            hand_type, multiplier = evaluate_dice_hand(dice)
            payout = bet * multiplier
            
            # Create the sorted dice image for the result
            sorted_dice = sorted(dice)
            sorted_dice_image = create_dice_image(sorted_dice, hand_type)
            
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
                    description=f"Bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}",
                    color=0x00ff00,
                    timestamp=datetime.now(timezone.utc)
                )
                
                result_embed.add_field(name="Your Hand", value=f"**{hand_type}**", inline=False)
                result_embed.set_image(url="attachment://sorted_dice_roll.png")
                result_embed.add_field(
                    name="Result", 
                    value=f"Payout: {payout} {CURRENCY_PLURAL}\n"
                        f"Net win: {payout - bet} {CURRENCY_PLURAL}", 
                    inline=False
                )
                result_embed.add_field(
                    name="Balance", 
                    value=f"{new_balance} {CURRENCY_PLURAL}", 
                    inline=False
                )
            else:
                new_balance = current_balance - bet
                await cur.execute("UPDATE economy_data SET balance = ? WHERE user_id = ?", 
                                (new_balance, user_id))
                
                result_embed = discord.Embed(
                    title="Dice Poker - No win",
                    description=f"Bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}",
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
                    value=f"{new_balance} {CURRENCY_PLURAL}", 
                    inline=False
                )
                
            result_embed.set_footer(text=BOTVERSION)
            await msg.edit(embed=result_embed, attachments=[file])
        await con.commit()