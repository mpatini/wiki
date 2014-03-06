import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template

# create the app
app = Flask(__name__, instance_path='/var/www/wiki/instance')
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'wiki.db'),
    DEBUG=True,
    SECRET_KEY='development key',
))
app.config.from_envvar('WIKI_SETTINGS', silent=True)


"""
Setting up database
"""
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


"""
The View Functions
"""
push_title = ''

"""
# view a list of possible titles
@app.route('/')
def sidebar():
    db = get_db()
    cur = db.execute('SELECT title, text FROM entries ORDER BY id desc')
    entries = cur.fetchall()
    return render_template('base.html', entries=entries)
"""

# homepage
@app.route('/')
def homepage():
    global push_title
    push_title = '|'
    title = push_title
    entry = query_db("SELECT * FROM entries WHERE title = ?", [title], one=True)
    if entry is None:
        return redirect(url_for('edit_homepage', title=title))
    else:
        return render_template("wiki.html", entry=entry['text'])

# individual wiki page
@app.route("/<title>")
def viewpage(title):
    global push_title
    push_title = title
    entry = query_db("SELECT * FROM entries WHERE title = ?", [title], one=True)
    if entry is None:
        return redirect(url_for('editpage', title=title))
    else:
        return render_template("wiki.html", entry=entry['text'])
        
@app.route("/history")
def history():
    return "We are in development"

# edit handler just for no addon
@app.route('/edit')
def edit_homepage():
    return render_template("edit.html", title='|')

# edit the wiki page
@app.route('/edit/<title>')
def editpage(title):
	return render_template("edit.html", title=title)

# add the new entry from the editpage handler
@app.route('/add/<title>', methods=['POST'])
def add_entry(title):
    db = get_db()
    db.execute('INSERT INTO entries (title, text) VALUES (?, ?)',
                 [title, request.form['content']])
    db.commit()
    #flash('New entry was successfully posted')
    if title == "|":
        return redirect(url_for('homepage'))
    return redirect(url_for('viewpage', title=title))

@app.route('/update_edit')
def update_home():
    entry = query_db("SELECT * FROM entries WHERE title = |", one=True)
    return render_template("edit.html", title='|', update=True, text=entry['text'])

@app.route('/update_edit/<title>')
def update_edit(title):
    entry = query_db("SELECT * FROM entries WHERE title = ?", [title], one=True)
    return render_template("edit.html", title=title, update=True, text=entry['text'])

@app.route('/update/<title>', methods=['POST'])
def update_entry(title):
    db = get_db()
    db.execute('UPDATE entries SET text=? WHERE title=?', (request.form['content'], title))
    db.commit()
    if title == "|":
        return redirect(url_for('homepage'))
    return redirect(url_for('viewpage', title=title))

@app.context_processor
def push_title():
    global push_title
    return dict(title=push_title)





if __name__ == '__main__':
    init_db()
    app.run(debug=True)#host='107.170.69.45'


# I really think that Michael sucks. He keeps trying to push all his website propaganda onto me. I don't want his propaganda. I am an independent thinker. And also a little drunk. I was just drinking margaritas at Copa. Happy Wednesday!