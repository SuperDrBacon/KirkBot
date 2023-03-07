import numpy, re
import os
import sqlite3
from pathlib import Path
from urllib import request

path = os.path.abspath(os.getcwd())

setup_table = '''CREATE TABLE IF NOT EXISTS log_data(
                    ID                      INTEGER     PRIMARY KEY,
                    SERVER_NAME             TEXT,
                    SERVER_ID               INTEGER,
                    CHANNEL_NAME            TEXT,
                    CHANNEL_ID              INTEGER,
                    USERNAME                TEXT,
                    USER_ID                 INTEGER,
                    MESSAGE                 TEXT,
                    MESSAGE_ID              INTEGER,
                    IS_REPLY                INTEGER,
                    ORIGINAL_USERNAME       TEXT,
                    ORIGINAL_USER_ID        INTEGER,
                    ORIGINAL_MESSAGE        TEXT,
                    ORIGINAL_MESSAGE_ID     INTEGER,
                    DATE_TIME               TEXT,
                    UNIX_TIME               INTEGER);'''

def checkForFile(filepath, filename, database=False):
    if os.path.isfile(os.path.join(filepath, filename)):
        print (f"{filename} exists")
    elif database == False:
        try:
            open(f'{os.path.join(filepath, filename)}', "x").close
        except FileExistsError:
            print ("Somehow tried to create a file that already exists whilst failing os.path.isfile. Something is definitely brokey.")
        else:
            print (f"{filename} created")
    elif database == True:
        try:
            con = sqlite3.connect(f'{path}/cogs/log_data.db')
            cur = con.cursor()
            cur.execute(setup_table)
            con.commit()
        except Exception as error:
            print("Failed to make sqlite3 database:", error)
        finally:
            if con:
                cur.close()
                con.close()
                print ("sqlite3 database created")
    else:
        print("Something is wrong with the checkForFile function.")

def checkForDir(filepath):
    if os.path.isdir(filepath):
        print (f"{filepath} exists")	
    else:
        try:
            Path(filepath).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            print ("Somehow tried to create a file that already exists whilst failing os.path.isdir. Something is definitely brokey.")
        else:
            print (f"{filepath} created")




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

def isLink(message):
    request_response = request.head(message)
    status_code = request_response.status_code
    # website_is_up = status_code == 200
    if status_code == 200:
        print(3)
        return True
    else:
        print(4)
        return False

def getlink(message):
    request_response = request.head(message)
    status_code = request_response.status_code
    if status_code == 200:
        return message
    else:
        return None


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