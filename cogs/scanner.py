import discord, functions, datetime, time
from discord.ext import commands





class scanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('scanner module online')
    
    # @commands.has_permissions(administrator=True)
    # @commands.command()
    # async def scam(ctx, *, message):
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot:
            return
        if ctx.guild.id == 937056927312150599:
            # print('neger')
            distance = {}
            message = ctx.content
            URLs = functions.findURLs(message)
            joinDate = ctx.author.joined_at
            currentTime = datetime.datetime.now().astimezone()
            timeDifference = currentTime - joinDate
            scam = {"reason":[], "percentage":0}

            for url in URLs:
                #Iterating over all URLs found in the message.

                dist = functions.levenshteinDistanceDP(url, "https://discord.com")
                distance[url] = dist
                #Getting the distance between an actual Discord URL and a fake one.

                if url in functions.scamLinks:
                    #If URL is in known scam URLs, set scam to True.
                    scam['reason'].append(f"URL ({url}) is a verified scam link.")
                    scam['percentage'] = 100

            for word in functions.scamWordsList:
                #Iterating over all words scammers commonly use.
                if word in message.lower():
                    scam['percentage'] += 10
                    scam['reason'].append(f"Word ({word}) is suspicious word.")

            for url, distance in distance.items():
                #Going through all URLs found in the message and checking if they are close to a Discord URL.
                if distance <= 7:
                    if distance != 0:
                        scam['percentage'] += 20
                        scam['reason'].append(f"URL ({url}) is suspicious.")

            if timeDifference is not None:
                if int(timeDifference.days) <= 1:
                    #Checks to see if user has been a part of the server for less than a day before sending this message.
                    scam['percentage'] += 30
                    scam['reason'].append(f"Age in server (<t:{int(time.mktime(joinDate.timetuple()))}:R>) is suspicious.")

            #await ctx.send(f"{scam['percentage']}% likely to be a scam.")
            x = '\n'.join(scam['reason'])
            
            if int(scam['percentage']) >= 50:
                await ctx.channel.send(embed=discord.Embed(title=f"{scam['percentage']}% likely to be a scam.", description=f"Reason(s): {x}", color=0x126180))
            else:
                pass

            # await ctx.channel.send(embed=discord.Embed(title="All Data.").add_field(name="Returned -", value=scam).add_field(name="URLs -", value=URLs))
        else:
            pass
def setup(bot):
    bot.add_cog(scanner(bot))