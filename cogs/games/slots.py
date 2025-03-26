import asyncio
import random
import aiosqlite
import discord

from datetime import datetime, timezone
from cogs.utils.constants import BOTVERSION, CURRENCY_PLURAL, CURRENCY_SINGULAR, ECONOMY_DATABASE, MSG_DEL_DELAY, SLOT_SYMBOLS, SLOTS_ROTATE_DELAY

async def slots_command(ctx, bet):
        user_id = ctx.author.id
        
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance, slots_wins, slots_losses FROM economy_data WHERE user_id = ?", (user_id,))
                current_balance, slots_wins, slots_losses = await cur.fetchone()
                
                if current_balance < bet:
                    msg = await ctx.reply(f"You don't have enough {CURRENCY_PLURAL} to play Slots with a bet of {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}. Your current balance is only {current_balance} {CURRENCY_SINGULAR if current_balance == 1 else CURRENCY_PLURAL}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                elif bet <= 0:
                    msg = await ctx.reply(f"You can't bet {bet} {CURRENCY_PLURAL}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                
                slot_grid = [[random.choice(list(SLOT_SYMBOLS.keys())) for _ in range(3)] for _ in range(3)]
                embed = discord.Embed(title="Slot Machine", description=f"bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}", color=0x00ff00, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="\u200b",  value=f"{slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n\
                                                        {slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n\
                                                        {slot_grid[2][0]} {slot_grid[2][1]} {slot_grid[2][2]}", inline=False)
                
                embed.set_footer(text=BOTVERSION)
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
                    result_embed = discord.Embed(title="Slot Machine", description=f"bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}\n\
                                                                                    {slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n\
                                                                                    {slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n\
                                                                                    {slot_grid[2][0]} {slot_grid[2][1]} {slot_grid[2][2]}\n\n\
                                                                                    You won {payout} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}!\
                                                                                    Your new balance is {current_balance + payout} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}.\n\
                                                                                    You have won {slots_wins} {'time' if slots_wins == 1 else 'times'} and lost {slots_losses} {'time' if slots_losses == 1 else 'times'}.", color=0x00ff00, timestamp=datetime.now(timezone.utc))
                else:
                    new_balance = current_balance - bet
                    await cur.execute("UPDATE economy_data SET balance = ?, slots_losses = slots_losses + 1 WHERE user_id = ?", (new_balance, user_id,))
                    slots_losses += 1
                    result_embed = discord.Embed(title="Slot Machine", description=f"bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}\n\
                                                                                    {slot_grid[0][0]} {slot_grid[0][1]} {slot_grid[0][2]}\n\
                                                                                    {slot_grid[1][0]} {slot_grid[1][1]} {slot_grid[1][2]}\n\
                                                                                    {slot_grid[2][0]} {slot_grid[2][1]} {slot_grid[2][2]}\n\n\
                                                                                    You lost {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}.\
                                                                                    Your new balance is {current_balance - bet} {CURRENCY_SINGULAR if current_balance - bet == 1 else CURRENCY_PLURAL}.\n\
                                                                                    You have won {slots_wins} {'time' if slots_wins == 1 else 'times'} and lost {slots_losses} {'time' if slots_losses == 1 else 'times'}.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                
                result_embed.set_footer(text=BOTVERSION)
                await msg.edit(embed=result_embed)
            await con.commit()