from functools import partial
import numpy, re
import shutil
import os

def filter(message):
    emojipattern = r'<.*?>'
    text2 = re.sub(emojipattern, '', message)

    commandpluspattern = r'\+([\S]+.)'
    text3 = re.sub(commandpluspattern, '', text2)

    links = r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,10}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'
    text4 = re.sub(links, '', text3)

    commanddotpattern = r'\.([\S]+.)'
    text5 = re.sub(commanddotpattern, '', text4)

    commandcommapattern = r'\,([\S]+.)'
    text6 = re.sub(commandcommapattern, '', text5)

    leadingspacespattern = r'^ +'
    text7 = re.sub(leadingspacespattern, '', text6)

    exclamationpattern = r'\!([\S]+.)'
    text8 = re.sub(exclamationpattern, '', text7)

    atpattern = r'\@([\S]+.)'
    text9 = re.sub(atpattern, '', text8)
    
    dashdashpattern = r'--([\S]+.)'
    text10 = re.sub(dashdashpattern, '', text9)
    
    gdotpattern = r'(g|G)\.([\S]+.)'
    cleaned = re.sub(gdotpattern, '', text10)
    
    # newline = '\n'
    # text10 = re.sub(newline, ' ', text9)
    
    return cleaned


messagestxt = os.path.abspath(os.getcwd()) + "/jsonLogToMessages.txt"
genAI_log = os.path.abspath(os.getcwd()) + "/genAI_log.txt"
messages = os.path.abspath(os.getcwd()) + "/messages.txt"

def joinfiles():
    with open(messages,'wb') as wfd:
        for f in [genAI_log, messagestxt]:
            with open(f, 'rb') as fd:
                shutil.copyfileobj(fd, wfd)
    with open(messages, 'rb') as linecount:
        lines = 0
        buf_size = 1024 * 1024
        read_f = linecount.raw.read

        buf = read_f(buf_size)
        while buf:
            lines += buf.count(b'\n')
            buf = read_f(buf_size)
    return lines




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