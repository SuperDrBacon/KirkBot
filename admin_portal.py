import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime

import aiosqlite
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO

from cogs.utils.constants import (ARCHIVE_DATABASE, COMMAND_LOGS_DATABASE,
                                  INVITELOG_DATABASE)

# Disable Flask's built-in logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'kirkbot-secret-key'

# Disable Flask console output
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

# Configure SocketIO to be silent
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

def run_flask(host='0.0.0.0', port=5005, debug=False):
    socketio.run(app, host=host, port=port, debug=debug, use_reloader=True)

def read_database_data():
    con = sqlite3.connect(ARCHIVE_DATABASE)
    # Note: Added server_id to the SELECT query
    cur = con.execute('SELECT server_name, channel_name, username, message, is_reply, original_username, original_message, server_id FROM archive_data ORDER BY rowid DESC')
    server_data = cur.fetchall()

    servers = {}
    for row in server_data:
        server_name, channel_name, username, message, is_reply, original_username, original_message, server_id = row
        server_id = str(server_id)
        
        # Use server_id as the key instead of server_name
        if server_id not in servers:
            servers[server_id] = {
                'name': server_name,  # Store the server name for display
                'messages': []
            }

        if is_reply == 1:
            message_obj = {
                "server_name": server_name,
                "channel_name": channel_name,
                "username": username,
                "message": message,
                "is_reply": True,
                "original_username": original_username,
                "original_message": original_message,
                "timestamp": ""  # Add timestamp if available in your database
            }
        else:
            message_obj = {
                "server_name": server_name,
                "channel_name": channel_name,
                "username": username,
                "message": message,
                "is_reply": False,
                "timestamp": ""  # Add timestamp if available in your database
            }

        servers[server_id]['messages'].append(message_obj)
        
        if len(servers[server_id]['messages']) > 100:
            servers[server_id]['messages'] = servers[server_id]['messages'][:100]

    return servers

# API endpoint to receive new messages from the bot
@app.route('/api/new_message', methods=['POST'])
def new_message():
    message_data = request.json
    
    # Extract message data
    server_name = message_data.get('server_name', '')
    server_id = str(message_data.get('server_id', ''))  # Convert to string for consistency
    channel_name = message_data.get('channel_name', '')
    username = message_data.get('username', '')
    message = message_data.get('message', '')
    is_reply = message_data.get('is_reply', 0)
    
    # Create message object for the client
    if is_reply == 1:
        original_username = message_data.get('original_username', '')
        original_message = message_data.get('original_message', '')
        client_data = {
            'server_id': server_id,
            'server_name': server_name,
            'message': {
                "server_name": server_name,
                "channel_name": channel_name,
                "username": username,
                "message": message,
                "is_reply": True,
                "original_username": original_username,
                "original_message": original_message,
                "timestamp": ""  # Add timestamp if available
            }
        }
    else:
        client_data = {
            'server_id': server_id,
            'server_name': server_name,
            'message': {
                "server_name": server_name,
                "channel_name": channel_name,
                "username": username,
                "message": message,
                "is_reply": False,
                "timestamp": ""  # Add timestamp if available
            }
        }
    
    # Emit the message to all connected clients
    socketio.emit('new_message', client_data)
    
    return jsonify({"status": "success"})

# API endpoint to receive new command usage from the bot
@app.route('/api/new_command', methods=['POST'])
def new_command():
    command_data = request.json
    
    # Emit the command to all connected clients
    socketio.emit('new_command', command_data)
    
    return jsonify({"status": "success"})

@app.route('/')
def index():
    # Get some basic stats for the homepage
    stats_data = {"servers": 0, "users": 0, "messages": 0}
    commands_data = {"total_commands": 0, "active_invites": 0}
    
    try:
        # Get server, user and message stats
        con = sqlite3.connect(ARCHIVE_DATABASE)
        cur = con.cursor()
        
        cur.execute("SELECT COUNT(DISTINCT SERVER_ID) FROM archive_data")
        stats_data["servers"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT USER_ID) FROM archive_data")
        stats_data["users"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM archive_data")
        stats_data["messages"] = cur.fetchone()[0]
        
        con.close()
        
        # Get command stats
        con = sqlite3.connect(COMMAND_LOGS_DATABASE)
        cur = con.cursor()
        
        cur.execute("SELECT COUNT(*) FROM command_logs")
        commands_data["total_commands"] = cur.fetchone()[0]
        
        con.close()
        
        # Get active invites
        con = sqlite3.connect(INVITELOG_DATABASE)
        cur = con.cursor()
        
        current_time = int(time.time())
        cur.execute("SELECT COUNT(*) FROM invitelog WHERE EXPIRATION_DATE_UNIX > ?", (current_time,))
        commands_data["active_invites"] = cur.fetchone()[0]
        
        con.close()
    except Exception as e:
        print(f"Error getting homepage stats: {e}")
    
    return render_template('homepage.html', stats_data=stats_data, commands_data=commands_data)

@app.route('/stats')
def stats():
    # Initialize stats data structure
    stats_data = {
        "servers": 0, 
        "users": 0, 
        "messages": 0,
        "top_servers": [],
        "top_users": [],
        "message_timeline": [],
        "channel_activity": [],
        "commands_today": 0,
        "active_invites": 0
    }
    
    # Get actual statistics from database
    try:
        con = sqlite3.connect(ARCHIVE_DATABASE)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        # Count unique servers
        cur.execute("SELECT COUNT(DISTINCT SERVER_ID) FROM archive_data")
        stats_data["servers"] = cur.fetchone()[0]
        
        # Count unique users
        cur.execute("SELECT COUNT(DISTINCT USER_ID) FROM archive_data")
        stats_data["users"] = cur.fetchone()[0]
        
        # Count total messages
        cur.execute("SELECT COUNT(*) FROM archive_data")
        stats_data["messages"] = cur.fetchone()[0]
        
        # Get top 5 servers by message count
        cur.execute("""
            SELECT server_name, COUNT(*) as message_count
            FROM archive_data 
            GROUP BY server_id, server_name
            ORDER BY message_count DESC 
            LIMIT 5
        """)
        stats_data["top_servers"] = [dict(row) for row in cur.fetchall()]
        
        # Get top 5 users by message count
        cur.execute("""
            SELECT username, COUNT(*) as message_count
            FROM archive_data 
            GROUP BY user_id, username
            ORDER BY message_count DESC 
            LIMIT 5
        """)
        stats_data["top_users"] = [dict(row) for row in cur.fetchall()]
        
        # Get message activity over the last 30 days (or available data)
        cur.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM archive_data 
            WHERE timestamp IS NOT NULL
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        """)
        timeline_data = cur.fetchall()
        stats_data["message_timeline"] = [dict(row) for row in reversed(timeline_data)]
        
        # Get top channels by message count
        cur.execute("""
            SELECT channel_name, server_name, COUNT(*) as message_count
            FROM archive_data 
            GROUP BY channel_name, server_name
            ORDER BY message_count DESC 
            LIMIT 10
        """)
        stats_data["channel_activity"] = [dict(row) for row in cur.fetchall()]
        
        con.close()
        
        # Get command statistics
        try:
            con = sqlite3.connect(COMMAND_LOGS_DATABASE)
            cur = con.cursor()
            
            # Commands used today
            cur.execute("""
                SELECT COUNT(*) FROM command_logs 
                WHERE DATE(timestamp) = DATE('now')
            """)
            result = cur.fetchone()
            if result:
                stats_data["commands_today"] = result[0]
            
            con.close()
        except Exception as e:
            print(f"Error getting command stats: {e}")
            
        # Get invite statistics
        try:
            con = sqlite3.connect(INVITELOG_DATABASE)
            cur = con.cursor()
            
            current_time = int(time.time())
            cur.execute("SELECT COUNT(*) FROM invitelog WHERE EXPIRATION_DATE_UNIX > ? OR EXPIRATION_DATE_UNIX = 0", (current_time,))
            result = cur.fetchone()
            if result:
                stats_data["active_invites"] = result[0]
            
            con.close()
        except Exception as e:
            print(f"Error getting invite stats: {e}")
            
    except Exception as e:
        print(f"Error getting stats: {e}")
    
    return render_template('stats.html', stats_data=stats_data)

@app.route('/commands')
def commands():
    # Command data structure
    commands_data = {
        "recent_commands": [],
        "most_used": [],
        "top_users": [],
        "total_commands": 0
    }
    
    try:
        con = sqlite3.connect(COMMAND_LOGS_DATABASE)
        con.row_factory = sqlite3.Row  # This allows accessing columns by name
        cur = con.cursor()
        
        # Get total commands count
        cur.execute("SELECT COUNT(*) as count FROM command_logs")
        result = cur.fetchone()
        if result:
            commands_data["total_commands"] = result["count"]
        
        # Get recent commands
        cur.execute("""
            SELECT command_name, args, username, server_name, channel_name, timestamp
            FROM command_logs 
            ORDER BY timestamp DESC 
            LIMIT 50
        """)
        
        recent_commands = cur.fetchall()
        for cmd in recent_commands:
            commands_data["recent_commands"].append({
                "command_name": cmd["command_name"],
                "args": cmd["args"] if cmd["args"] else "",
                "username": cmd["username"],
                "server_name": cmd["server_name"],
                "channel_name": cmd["channel_name"],
                "timestamp": cmd["timestamp"]
            })
        
        # Get most used commands
        cur.execute("""
            SELECT command_name, COUNT(*) as count, MAX(timestamp) as last_used
            FROM command_logs
            GROUP BY command_name
            ORDER BY count DESC
            LIMIT 10
        """)
        
        most_used = cur.fetchall()
        for cmd in most_used:
            commands_data["most_used"].append({
                "command_name": cmd["command_name"],
                "count": cmd["count"],
                "last_used": cmd["last_used"]
            })
        
        # Get top command users
        cur.execute("""
            SELECT username, COUNT(*) as count, 
                (SELECT command_name FROM command_logs c2 
                    WHERE c2.username = c1.username 
                    GROUP BY command_name 
                    ORDER BY COUNT(*) DESC LIMIT 1) as favorite_command
            FROM command_logs c1
            GROUP BY username
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_users = cur.fetchall()
        for user in top_users:
            commands_data["top_users"].append({
                "username": user["username"],
                "count": user["count"],
                "favorite_command": user["favorite_command"]
            })
        
        con.close()
    except Exception as e:
        print(f"Error getting command data: {e}")
    
    return render_template('commands.html', commands_data=commands_data)

@app.route('/invites')
def invites():
    invites_data = {"invites": []}
    
    try:
        con = sqlite3.connect(INVITELOG_DATABASE)
        con.row_factory = sqlite3.Row  # This allows accessing columns by name
        cur = con.cursor()
        
        # Get all invite data
        try:
            cur.execute("""
                SELECT 
                    SERVER_ID, INVITE_CODE, CURRENT_USES, MAX_USES, 
                    INVITER_ID, INVITER_NAME, INVITE_CHANNEL_ID, EXPIRATION_DATE_UNIX
                FROM invitelog 
                ORDER BY EXPIRATION_DATE_UNIX DESC
            """)
            
            invites_data["invites"] = [tuple(row) for row in cur.fetchall()]
        except Exception as e:
            invites_data["invites"] = []
        
        # Get invite uses by user
        try:
            # First check if the users table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if cur.fetchone():
                cur.execute("""
                    SELECT 
                        u.INVITE_CODE, u.USED_BY_NAME, u.USED_BY_ID, 
                        i.INVITER_NAME, i.SERVER_ID
                    FROM users u
                    JOIN invitelog i ON u.INVITE_CODE = i.INVITE_CODE
                    ORDER BY u.USED_BY_ID
                """)
                
                invites_data["invite_uses"] = [tuple(row) for row in cur.fetchall()]
            else:
                invites_data["invite_uses"] = []
        except Exception:
            invites_data["invite_uses"] = []
        
        con.close()
    except Exception:
        pass
    
    return render_template('invites.html', invites_data=invites_data)

@app.route('/messages')
def messages():
    # Read server and message data
    page_data = read_database_data()
    return render_template('messages.html', page_data=page_data)

@app.template_filter('timestamp_to_date')
def timestamp_to_date(unix_timestamp):
    """Convert a Unix timestamp to a formatted date string"""
    if not unix_timestamp or unix_timestamp <= 0:
        return "Never"
    return datetime.fromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')

@app.template_filter('sum')
def sum_filter(iterable, attribute=None):
    """Sum values in an iterable, optionally extracting an attribute first"""
    if attribute is None:
        return sum(iterable)
    return sum(item[attribute] for item in iterable)

@app.context_processor
def utility_processor():
    def current_timestamp():
        """Return the current Unix timestamp"""
        return int(time.time())
    
    return dict(current_timestamp=current_timestamp)

if __name__ == '__main__':
    run_flask()