import asyncio
import random
import aiosqlite
import discord

from datetime import datetime, timezone
from cogs.utils.constants import BOTVERSION, CURRENCY_PLURAL, CURRENCY_SINGULAR, ECONOMY_DATABASE, MSG_DEL_DELAY


async def coinflip_command(ctx, guess, bet):
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
        async with aiosqlite.connect(ECONOMY_DATABASE) as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT balance, cf_wins, cf_losses FROM economy_data WHERE user_id = ?", (user_id,))
                current_balance, cf_wins, cf_losses = await cur.fetchone()
                
                if current_balance < bet:
                    msg = await ctx.reply(f"You don't have enough {CURRENCY_PLURAL} to play Coinflip with a bet of {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}. Your current balance is only {current_balance} {CURRENCY_SINGULAR if current_balance == 1 else CURRENCY_PLURAL}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                elif bet <= 0:
                    msg = await ctx.reply(f"You can't bet {bet} {CURRENCY_PLURAL}.")
                    await ctx.message.delete(delay=MSG_DEL_DELAY)
                    await msg.delete(delay=MSG_DEL_DELAY)
                    return
                
                outcome_possibilities = ["Heads", "Tails", "Edge"]
                outcome_weights = [0.49, 0.49, 0.02]
                coin = ''.join(random.choices(outcome_possibilities, outcome_weights)[0])
                
                embed = discord.Embed(title="Coinflip", description=f"bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}\nGuess: {guessed_coin}", color=0x00ff00, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Flipping coin", value='', inline=False)
                embed.set_footer(text=BOTVERSION)
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
                    result_embed = discord.Embed(title="Coinflip", description=f"bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}\n\
                                                                                Guess: {guessed_coin}\nResult: {coin}\n\nCongratulations! You won {payout} {CURRENCY_PLURAL}!\n\
                                                                                Your new balance is {current_balance + payout} {CURRENCY_PLURAL}.\n\
                                                                                You have won {cf_wins} {'time' if cf_wins == 1 else 'times'} and lost {cf_losses} {'time' if cf_losses == 1 else 'times'}.", color=0x00ff00, timestamp=datetime.now(timezone.utc))
                else:
                    cf_losses += 1
                    await cur.execute("UPDATE economy_data SET balance = balance - ?, cf_losses = cf_losses + 1 WHERE user_id = ?", (bet, user_id))
                    result_embed = discord.Embed(title="Coinflip", description=f"bet: {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}\n\
                                                                                Guess: {guessed_coin}\nResult: {coin}\n\nSorry, you lost {bet} {CURRENCY_SINGULAR if bet == 1 else CURRENCY_PLURAL}.\n\
                                                                                Your new balance is {current_balance - bet} {CURRENCY_SINGULAR if current_balance - bet == 1 else CURRENCY_PLURAL}.\n\
                                                                                You have won {cf_wins} {'time' if cf_wins == 1 else 'times'} and lost {cf_losses} {'time' if cf_losses == 1 else 'times'}.", color=0xff0000, timestamp=datetime.now(timezone.utc))
                result_embed.set_footer(text=BOTVERSION)
                await msg.edit(embed=result_embed)
            await con.commit()