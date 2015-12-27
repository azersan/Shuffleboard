# -*- coding: utf-8 -*-
"""
    Shuffleboard Tracking
"""

import os
import urlparse
import time
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flask.ext.mysqldb import MySQL
from contextlib import closing



# create our little application :)
app = Flask(__name__)

# Grab the clearDB config
url = urlparse.urlparse(os.environ['CLEARDB_DATABASE_URL'])
mysql = MySQL()

# Load default config and override config from an environment variable
app.config.update(dict(
    DEBUG = True,
    MYSQL_USER = url.username,
    MYSQL_PASSWORD = url.password,
    MYSQL_DB = url.path[1:],
    MYSQL_HOST = url.hostname,
    MYSQL_PORT = 3306,
    MYSQL_UNIX_SOCKET = None,
    MYSQL_CONNECT_TIMEOUT = None,
    MYSQL_READ_DEFAULT_FILE = None,
    MYSQL_USE_UNICODE=None,
    MYSQL_CHARSET=None,
    MYSQL_SQL_MODE=None,
    MYSQL_CURSORCLASS=None
))

def get_db():
    return mysql.connection

@app.route('/')
def get_main_page():
    return get_leaderboard()

@app.route('/players', methods=['GET', 'POST'])
def manage_players():
    if request.method == 'POST':
        return add_player(request)
    if request.method == 'GET':
        return get_leaderboard()

def add_player(request):
    db = get_db()
    db.cursor().execute('insert into players (name, wins, losses, rating) values (%s, 0, 0, 1500)',
        [request.form['name']])
    db.commit()
    return redirect(url_for('get_main_page'))

def get_leaderboard():
    cur = get_db().cursor()
    cur.execute('select id, name, wins, losses, rating from players order by rating desc')
    players = cur.fetchall()
    # for player in players:
    #     app.logger.debug('Row: %s', player)
    return render_template('home.html', players=players)

@app.route('/games', methods=['POST'])
def record_game():
    db = get_db()
    db.cursor().execute('insert into games (time_entered, red_player_one, red_player_two, blue_player_one, blue_player_two, red_score, blue_score) values (%s, %s, %s, %s, %s, %s, %s)',
        [int(round(time.time() * 1000)),
        request.form['redPlayer1'] or None,
        request.form['redPlayer2'] or None,
        request.form['bluePlayer1'] or None,
        request.form['bluePlayer2'] or None,
        request.form['redScore'],
        request.form['blueScore']])
    db.commit()
    update_stats(request)
    return redirect(url_for('get_main_page'))

def update_stats(request):
    update_stats_for_game(request.form['redPlayer1'] or None,
                          request.form['redPlayer2'] or None,
                          request.form['bluePlayer1'] or None,
                          request.form['bluePlayer2'] or None,
                          request.form['redScore'],
                          request.form['blueScore'])

def update_stats_for_game(redPlayer1, redPlayer2, bluePlayer1, bluePlayer2, redScore, blueScore):
    db = get_db()
    cur = db.cursor()
    cur.execute('select id, name, wins, losses, rating from players order by rating desc')
    players = cur.fetchall()

    results = {}
    results[int(redPlayer1)] = {'my_score' : redScore, 'their_score' : blueScore}
    results[int(redPlayer2)] = {'my_score' : redScore, 'their_score' : blueScore}
    results[int(bluePlayer1)] = {'my_score' : blueScore, 'their_score' : redScore}
    results[int(bluePlayer2)] = {'my_score' : blueScore, 'their_score' : redScore}

    for player in players:
        if player[0] in results:
            more_wins = 0
            more_losses = 0
            if int(results[player[0]]['my_score']) > int(results[player[0]]['their_score']):
                more_wins = 1
            else:
                more_losses = 1
            db.cursor().execute('update players set wins=%s, losses=%s where id=%s',
                [player[2] + more_wins, player[3] + more_losses, player[0]])
            db.commit()
    return

@app.route('/reload_stats', methods=['POST'])
def reload_status():
    app.logger.info('Reloading stats for all players')
    reset_stats()
    process_all_games()
    return redirect(url_for('get_main_page'))

def reset_stats():
    get_db().cursor().execute('update players set wins=0, losses=0, rating=1500')
    get_db().commit()

def process_all_games():
    cur = get_db().cursor()
    cur.execute('select red_player_one, red_player_two, blue_player_one, blue_player_two, red_score, blue_score, id from games order by time_entered asc')
    games = cur.fetchall()
    for game in games:
        app.logger.info('Processing game %s', game[6])
        update_stats_for_game(game[0], game[1], game[2], game[3], game[4], game[5])

if __name__ == "__main__":
    app.run()
