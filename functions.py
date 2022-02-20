import numpy, re
def levenshteinDistanceDP(token1, token2):
    distances = numpy.zeros((len(token1) + 1, len(token2) + 1))

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2
        
    a = 0
    b = 0
    c = 0
    
    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if (token1[t1-1] == token2[t2-1]):
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]
                b = distances[t1 - 1][t2]
                c = distances[t1 - 1][t2 - 1]
                
                if (a <= b and a <= c):
                    distances[t1][t2] = a + 1
                elif (b <= a and b <= c):
                    distances[t1][t2] = b + 1
                else:
                    distances[t1][t2] = c + 1
    return distances[len(token1)][len(token2)]


def findURLs(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string) 
    # >>> x = findURLs("hello https://google.com minecraft.net https://minecraft.net")
    # >>> x
    # [('https://google.com', '', '', '', ''), ('https://minecraft.net', '', '', '', '')]   
    return [Url[0] for Url in url]
    #Iterates over all elements in the list, which are tuples, and returns the 0th element, which is the URL.

scamWordsList = ["free", "steam", "nitro", "gift", "@everyone"]
scamLinks = [set([
    "https://dlscord-nitro.info/",
    "https://nitro-drop.com/",
    "https://discordgift.site/",
    "https://dlscordsteam.com/",
    "https://gamex.codes/",
    "https://discordnitrocodes.blogspot.com/",
    "https://shared-tools.xyz/",
    "https://techgenerator.xyz/",
    "https://steamcomminuty.com/",
    "https://rbuxfree.com/",
    "https://genrates.xyz/",
    "https://dlscord.org/",
    "https://psp-haxors.com/",
    "http://arcades.tech/",
    "https://discord.freehlp.com/",
    "https://sehotgame.xyz/",
    "https://www.appninjas.xyz/",
    "https://steamcomminutty.ru/",
    "https://discord.giveawey.com/",
    "https://steamsnitro.ru/",
    "https://discorcl-gift.ru/",
    "https://dlscorldnitro.store/",
    "https://steamdiscord.com/",
    "https://dlscord-app.com/",
    "https://discords-nitro.xyz/",
    "https://discord-drop.xyz/",
    "https://gift-g2.ru/",
    "https://discord-give.com/",
    "https://discord-app.net/",
    "https://discocrd-nitro.com/",
    "https://dlscord.org/",
    "https://dlscordsteam.com/",
    "https://discorcll.com/",
    "https://discorid.gift/",
    "https://dlscord-app.info/",
    "https://discord-app.uk/",
    "https://steancornminuty.com/",
    "https://dlscordnitro.com/",
    "https://disordapp.codes/",
    "https://dlscord.net/",
    "https://discordsgift.com/",
    "https://discordrgift.com/",
    "https://discordc.gift/",
    "https://dliscord.com/",
    "https://discorl.com/",
    "https://discorde.gift/",
    "https://dlscordniltro.com/",
    "https://dliscords.com/",
    "https://discordll.gift/",
    "https://discordd.gift/",
    "https://dilscord.com/",
    "https://discrocl-gift.xyz/",
    "https://boostnitro.shop/",
    "https://discord-nltro.xyz/",
    "https://discord.gifte.com/",
    "https://gifte.com/",
    "https://discocrd-gifts.com/",
    "https://dlscocrdapp.com/",
    "https://steamcommunityx.com/",
    "https://steams-csgo.com/",
    "https://steamcommunityx.com/",
    "https://dlscord.gift/",
    "https://discordrgift.ru",
    "https://discocrd.gift",
    "http://discord-airdrop.com",
    "https://discord-give.com"
])][0]

# Credit to https://github.com/Discord-AntiScam/scam-links/blob/main/urls.json