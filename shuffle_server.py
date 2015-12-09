# -*- coding: utf-8 -*-
"""
    Shuffleboard Tracking
"""

import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from contextlib import closing


# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'shuffleboard.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
# app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# @app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

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
    db.execute('insert into players (name, wins, losses, rating) values (?, 0, 0, 1500)',
        [request.form['name']])
    db.commit()
    return redirect(url_for('manage_players'))

def get_leaderboard():
    db = get_db()
    cur = db.execute('select id, name, wins, losses, rating from players order by rating desc')
    players = cur.fetchall()
    return render_template('home.html', players=players)

@app.route('/games', methods=['POST'])
def record_game():
    update_stats(request)
    return get_leaderboard()


def update_stats(request):
    results = {}
    results[int(request.form['redPlayer1'])] = {'my_score' : request.form['redScore'], 'their_score' : request.form['blueScore']}
    results[int(request.form['redPlayer2'])] = {'my_score' : request.form['redScore'], 'their_score' : request.form['blueScore']}
    results[int(request.form['bluePlayer1'])] = {'my_score' : request.form['blueScore'], 'their_score' : request.form['redScore']}
    results[int(request.form['bluePlayer2'])] = {'my_score' : request.form['blueScore'], 'their_score' : request.form['redScore']}
    app.logger.debug('Results: %s', results)
    db = get_db()
    cur = db.execute('select id, name, wins, losses, rating from players order by rating desc')
    players = cur.fetchall()

    for player in players:
        app.logger.debug("Player: %s", player[0])
        if player[0] in results:
            more_wins = 0
            more_losses = 0
            if results[player[0]]['my_score'] > results[player[0]]['their_score']:
                more_wins = 1
            else:
                more_losses = 1
            app.logger.debug('updating player %s', player[1])
            db.execute('update players set wins=?, losses=? where id=?',
                [player[2] + more_wins, player[3] + more_losses, player[0]])
            db.commit()
    return

if __name__ == "__main__":
    app.run()
