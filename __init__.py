import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template
from utils import get_datetime
from operator import itemgetter

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
Setting up primary database
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
versions = {}
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

# edit handler just for no addon
@app.route('/_edit')
def edit_homepage():
    return render_template("edit.html", title='|')

# edit the wiki page
@app.route('/edit/<title>')
def editpage(title):
	return render_template("edit.html", title=title)

# add the new entry from the editpage handler
@app.route('/add/<title>', methods=['POST'])
def add_entry(title):
    global versions
    versions[title] = 1
    current_date = get_datetime()
    db = get_db()
    db.execute('INSERT INTO entries (title, text, my_date, version) VALUES (?, ?, ?, ?)',
                 [title, request.form['content'], current_date, versions[title]])
    db.commit()
    #flash('New entry was successfully posted')
    if title == "|":
        return redirect(url_for('homepage'))
    return redirect(url_for('viewpage', title=title))


@app.route('/_update_edit')
def update_home():
    entry = query_db("SELECT * FROM entries WHERE title = ?", ["|"], one=True)
    return render_template("edit.html", title='|', update=True, text=entry['text'])

@app.route('/update_edit/<title>')
def update_edit(title):
    entry = query_db("SELECT * FROM entries WHERE title = ?", [title], one=True)
    return render_template("edit.html", title=title, update=True, text=entry['text'])

@app.route('/update/<title>', methods=['POST'])
def update_entry(title):
    global versions
    version = versions[title]
    versions[title] += 1
    current_date = get_datetime()
    db = get_db()
    # create a version
    entry = query_db("SELECT * FROM entries WHERE title = ?", [title], one=True)
    db.execute('INSERT INTO entries (title, text, my_date, version) VALUES (?, ?, ?, ?)',
                 [title + "v%s" % version, entry['text'], entry['my_date'], version])
    db.commit()
    # update entry
    db.execute('UPDATE entries SET text=?, my_date=?, version=? WHERE title=?', (request.form['content'], current_date, versions[title], title))
    db.commit()
    if title == "|":
        return redirect(url_for('homepage'))
    return redirect(url_for('viewpage', title=title))

@app.context_processor
def push_title():
    global push_title
    return dict(title=push_title)


"""
Primary History Functions
"""
@app.route("/_history")
def history_homepage():
    global push_title
    title = "|"
    push_title = title
    db = get_db()
    cur = db.execute('SELECT title, text, my_date, version FROM entries ORDER BY id desc')
    entries = cur.fetchall()
    # create list with appropriate names
    i = versions[title] - 1
    history = []
    while i >= 0:
        if i == 0:
            history.append([title])
        else:
            history.append([title + "v%s" % i])
        print "history: " + str(history)
        i -= 1
    # populate list
    for entry in entries:
        print "entry: " + str(entry['title'])
        for version in history:
            if entry['title'] == version[0]:
                version.append(entry['text'])
                version.append(entry['version'])
                version.append(entry['my_date'])
                print "history: " + str(history)
    print "history: " + str(history)
    history_sorted = sorted(history, key=itemgetter(2), reverse=True)
    return render_template("history_index.html", history=history_sorted, title=title)
    
@app.route("/history/<title>")
def history(title):
    global push_title
    push_title = title
    db = get_db()
    cur = db.execute('SELECT title, text, my_date, version FROM entries ORDER BY id desc')
    entries = cur.fetchall()
    # create list with appropriate names
    i = versions[title] - 1
    history = []
    while i >= 0:
        if i == 0:
            history.append([title])
        else:
            history.append([title + "v%s" % i])
        print "history: " + str(history)
        i -= 1
    # populate list
    for entry in entries:
        print "entry: " + str(entry['title'])
        for version in history:
            if entry['title'] == version[0]:
                version.append(entry['text'])
                version.append(entry['version'])
                version.append(entry['my_date'])
                print "history: " + str(history)
    print "history: " + str(history)
    history_sorted = sorted(history, key=itemgetter(2), reverse=True)
    return render_template("history_index.html", history=history_sorted, title=title)


"""
Current status:
    -history(title) currently doesn't create a list of links that
    can be edited, but rather creates a list of the titles
To do for history:
    -Must add links for that specific version
    -Write history function that is specific to homepage
    -Edit history link so that those related to the homepage have an _
    -Then: On to sessions

"""


"""
Sessions
"""





if __name__ == '__main__':
    init_db()
    app.run(debug=True)#host='107.170.69.45'


# I really think that Michael sucks. He keeps trying to push all his website propaganda onto me. I don't want his propaganda. I am an independent thinker. And also a little drunk. I was just drinking margaritas at Copa. Happy Wednesday!