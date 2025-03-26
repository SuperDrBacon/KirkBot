import os
from configparser import ConfigParser

#! File paths
OSPATH = os.path.abspath(os.getcwd())
CARDSPATH = rf'{OSPATH}/playingcards/'
DICEPATH = rf'{OSPATH}/dice/'
IMAGEPATH = rf'{OSPATH}/images/'
EMOJIPATH = rf'{OSPATH}/emojis/'
FLAGPATH = rf'{OSPATH}/cogs/flags.json'

AUTODELETE_DATABASE = rf'{OSPATH}/cogs/autodelete_data.db'
AUTOROLE_DATABASE = rf'{OSPATH}/cogs/autorole_data.db'
ARCHIVE_DATABASE = rf'{OSPATH}/cogs/archive_data.db'
COMMAND_LOGS_DATABASE = rf'{OSPATH}/cogs/command_logs.db'
ECONOMY_DATABASE = rf'{OSPATH}/cogs/economy_data.db'
INVITELOG_DATABASE = rf'{OSPATH}/cogs/invitelog_data.db'
PERMISSIONS_DATABASE = rf'{OSPATH}/cogs/permissions_data.db'

#! Config
info, config = ConfigParser(), ConfigParser()
info.read(rf'{OSPATH}/info.ini')
config.read(rf'{OSPATH}/config.ini')

STATUS = info['STATUS']['status']
COMMAND_PREFIX = config['BOTCONFIG']['prefix']
CURRENCY_SINGULAR = info['ECONOMY']['currency_singular']
CURRENCY_PLURAL = info['ECONOMY']['currency_plural']

TOKEN = config['BOTCONFIG']['token']
OWNER_ID = int(config['BOTCONFIG']['ownerid'])
BOTID = int(config['BOTCONFIG']['botID'])
BOTVERSION = info['DEFAULT']['title'] + ' v' + info['DEFAULT']['version']

#! Universal message delete delay
MSG_DEL_DELAY = 10

#! Websocket url
# WebSocket notification endpoint - used to notify the admin portal
ADMIN_PORTAL_WS_URL = "http://localhost:5000/api/new_message"

#! Bot status update delay
STATUS_LOOP_DELAY = 10

#! Markov ai constants
ORDER = 4
TEXT_WORD_COUNT = ORDER * 15 
MEME_WORD_COUNT = ORDER * 5

#! Fun cog constants
IMAGE_SIZE = 854, 480
GCP_DELAY = 1
NUM_OF_RANKED_WORDS = 5

#! Autodelete constants
SECOND_LOOP_DELAY = 5
TIME_UNITS = {  
    's':        ('second',  'seconds',  1),
    'sec':      ('second',  'seconds',  1),
    'secs':     ('second',  'seconds',  1),
    'second':   ('second',  'seconds',  1),
    'seconds':  ('second',  'seconds',  1),
    'm':        ('minute',  'minutes',  60),
    'min':      ('minute',  'minutes',  60),
    'mins':     ('minute',  'minutes',  60),
    'minute':   ('minute',  'minutes',  60),
    'minutes':  ('minute',  'minutes',  60),
    'h':        ('hour',    'hours',    3600),
    'hr':       ('hour',    'hours',    3600),
    'hrs':      ('hour',    'hours',    3600),
    'hour':     ('hour',    'hours',    3600),
    'hours':    ('hour',    'hours',    3600),
    'd':        ('day',     'days',     86400),
    'day':      ('day',     'days',     86400),
    'days':     ('day',     'days',     86400),
    'w':        ('week',    'weeks',    604800),
    'week':     ('week',    'weeks',    604800),
    'weeks':    ('week',    'weeks',    604800),
    'month':    ('month',   'months',   2592000),
    'months':   ('month',   'months',   2592000)}

#!# Game constants
STARTING_BALANCE = 1000
STARTING_BANK = 0
# ONE_DAY = 86400
ONE_DAY = 1
SLOTS_ROTATE_DELAY = 0.4
SLOT_SYMBOLS = {
    "🍒": 2,
    "🍊": 3,
    "🍋": 4,
    "🍉": 5,
    "🍇": 6,
    "🍎": 7,
    "🍓": 8,
    "🍍": 10,
    "💰": 20}

CARDS = {
    'clubs_2':          ('Clubs',     'black',  '♣',    '2',        f'{CARDSPATH}clubs_2.png'),
    'clubs_3':          ('Clubs',     'black',  '♣',    '3',        f'{CARDSPATH}clubs_3.png'),
    'clubs_4':          ('Clubs',     'black',  '♣',    '4',        f'{CARDSPATH}clubs_4.png'),
    'clubs_5':          ('Clubs',     'black',  '♣',    '5',        f'{CARDSPATH}clubs_5.png'),
    'clubs_6':          ('Clubs',     'black',  '♣',    '6',        f'{CARDSPATH}clubs_6.png'),
    'clubs_7':          ('Clubs',     'black',  '♣',    '7',        f'{CARDSPATH}clubs_7.png'),
    'clubs_8':          ('Clubs',     'black',  '♣',    '8',        f'{CARDSPATH}clubs_8.png'),
    'clubs_9':          ('Clubs',     'black',  '♣',    '9',        f'{CARDSPATH}clubs_9.png'),
    'clubs_10':         ('Clubs',     'black',  '♣',    '10',       f'{CARDSPATH}clubs_10.png'),
    'clubs_jack':       ('Clubs',     'black',  '♣',    'Jack',     f'{CARDSPATH}clubs_jack.png'),
    'clubs_queen':      ('Clubs',     'black',  '♣',    'Queen',    f'{CARDSPATH}clubs_queen.png'),
    'clubs_king':       ('Clubs',     'black',  '♣',    'King',     f'{CARDSPATH}clubs_king.png'),
    'clubs_ace':        ('Clubs',     'black',  '♣',    'Ace',      f'{CARDSPATH}clubs_ace.png'),
    'diamonds_2':       ('Diamonds',  'red',    '♦',    '2',        f'{CARDSPATH}diamonds_2.png'),
    'diamonds_3':       ('Diamonds',  'red',    '♦',    '3',        f'{CARDSPATH}diamonds_3.png'),
    'diamonds_4':       ('Diamonds',  'red',    '♦',    '4',        f'{CARDSPATH}diamonds_4.png'),
    'diamonds_5':       ('Diamonds',  'red',    '♦',    '5',        f'{CARDSPATH}diamonds_5.png'),
    'diamonds_6':       ('Diamonds',  'red',    '♦',    '6',        f'{CARDSPATH}diamonds_6.png'),
    'diamonds_7':       ('Diamonds',  'red',    '♦',    '7',        f'{CARDSPATH}diamonds_7.png'),
    'diamonds_8':       ('Diamonds',  'red',    '♦',    '8',        f'{CARDSPATH}diamonds_8.png'),
    'diamonds_9':       ('Diamonds',  'red',    '♦',    '9',        f'{CARDSPATH}diamonds_9.png'),
    'diamonds_10':      ('Diamonds',  'red',    '♦',    '10',       f'{CARDSPATH}diamonds_10.png'),
    'diamonds_jack':    ('Diamonds',  'red',    '♦',    'Jack',     f'{CARDSPATH}diamonds_jack.png'),
    'diamonds_queen':   ('Diamonds',  'red',    '♦',    'Queen',    f'{CARDSPATH}diamonds_queen.png'),
    'diamonds_king':    ('Diamonds',  'red',    '♦',    'King',     f'{CARDSPATH}diamonds_king.png'),
    'diamonds_ace':     ('Diamonds',  'red',    '♦',    'Ace',      f'{CARDSPATH}diamonds_ace.png'),
    'hearts_2':         ('Hearts',    'red',    '♥',    '2',        f'{CARDSPATH}hearts_2.png'),
    'hearts_3':         ('Hearts',    'red',    '♥',    '3',        f'{CARDSPATH}hearts_3.png'),
    'hearts_4':         ('Hearts',    'red',    '♥',    '4',        f'{CARDSPATH}hearts_4.png'),
    'hearts_5':         ('Hearts',    'red',    '♥',    '5',        f'{CARDSPATH}hearts_5.png'),
    'hearts_6':         ('Hearts',    'red',    '♥',    '6',        f'{CARDSPATH}hearts_6.png'),
    'hearts_7':         ('Hearts',    'red',    '♥',    '7',        f'{CARDSPATH}hearts_7.png'),
    'hearts_8':         ('Hearts',    'red',    '♥',    '8',        f'{CARDSPATH}hearts_8.png'),
    'hearts_9':         ('Hearts',    'red',    '♥',    '9',        f'{CARDSPATH}hearts_9.png'),
    'hearts_10':        ('Hearts',    'red',    '♥',    '10',       f'{CARDSPATH}hearts_10.png'),
    'hearts_jack':      ('Hearts',    'red',    '♥',    'Jack',     f'{CARDSPATH}hearts_jack.png'),
    'hearts_queen':     ('Hearts',    'red',    '♥',    'Queen',    f'{CARDSPATH}hearts_queen.png'),
    'hearts_king':      ('Hearts',    'red',    '♥',    'King',     f'{CARDSPATH}hearts_king.png'),
    'hearts_ace':       ('Hearts',    'red',    '♥',    'Ace',      f'{CARDSPATH}hearts_ace.png'),
    'spades_2':         ('Spades',    'black',  '♠',    '2',        f'{CARDSPATH}spades_2.png'),
    'spades_3':         ('Spades',    'black',  '♠',    '3',        f'{CARDSPATH}spades_3.png'),
    'spades_4':         ('Spades',    'black',  '♠',    '4',        f'{CARDSPATH}spades_4.png'),
    'spades_5':         ('Spades',    'black',  '♠',    '5',        f'{CARDSPATH}spades_5.png'),
    'spades_6':         ('Spades',    'black',  '♠',    '6',        f'{CARDSPATH}spades_6.png'),
    'spades_7':         ('Spades',    'black',  '♠',    '7',        f'{CARDSPATH}spades_7.png'),
    'spades_8':         ('Spades',    'black',  '♠',    '8',        f'{CARDSPATH}spades_8.png'),
    'spades_9':         ('Spades',    'black',  '♠',    '9',        f'{CARDSPATH}spades_9.png'),
    'spades_10':        ('Spades',    'black',  '♠',    '10',       f'{CARDSPATH}spades_10.png'),
    'spades_jack':      ('Spades',    'black',  '♠',    'Jack',     f'{CARDSPATH}spades_jack.png'),
    'spades_queen':     ('Spades',    'black',  '♠',    'Queen',    f'{CARDSPATH}spades_queen.png'),
    'spades_king':      ('Spades',    'black',  '♠',    'King',     f'{CARDSPATH}spades_king.png'),
    'spades_ace':       ('Spades',    'black',  '♠',    'Ace',      f'{CARDSPATH}spades_ace.png'),
    'card_back':        ('Card',      'void',   '■',    'Back',     f'{CARDSPATH}card_back.png'),
    'joker_black':      ('Joker',     'black',  '🤡',   'Black',    f'{CARDSPATH}joker_black.png'),
    'joker_red':        ('Joker',     'red',    '🤡',   'Red',      f'{CARDSPATH}joker_red.png')}

# Color variants for dice faces
DICE = {
    # Each dice number has color variants
    1: {
        'white': f'{DICEPATH}one_white.png',
        'red': f'{DICEPATH}one_red.png',
        'green': f'{DICEPATH}one_green.png'
    },
    2: {
        'white': f'{DICEPATH}two_white.png',
        'red': f'{DICEPATH}two_red.png',
        'green': f'{DICEPATH}two_green.png'
    },
    3: {
        'white': f'{DICEPATH}three_white.png',
        'red': f'{DICEPATH}three_red.png',
        'green': f'{DICEPATH}three_green.png'
    },
    4: {
        'white': f'{DICEPATH}four_white.png',
        'red': f'{DICEPATH}four_red.png',
        'green': f'{DICEPATH}four_green.png'
    },
    5: {
        'white': f'{DICEPATH}five_white.png',
        'red': f'{DICEPATH}five_red.png',
        'green': f'{DICEPATH}five_green.png'
    },
    6: {
        'white': f'{DICEPATH}six_white.png',
        'red': f'{DICEPATH}six_red.png',
        'green': f'{DICEPATH}six_green.png'
    }
}

CARD_SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
CARD_RANKS = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']
CARD_VALUES = {'Ace': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'Jack': 10, 'Queen': 10, 'King': 10}
