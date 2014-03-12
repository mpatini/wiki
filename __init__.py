import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, render_template
from utils import get_datetime, trunc_version, valid_username, valid_password
from operator import itemgetter
from flaskext.bcrypt import Bcrypt
from secret import secret

# create the app
app = Flask(__name__, instance_path='/var/www/wiki/instance')
app.config.from_object(__name__)
bcrypt = Bcrypt(app)

app.config.update(dict(
    DATABASE=os.path.join(app.instance_path, 'wiki.db'),
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
push_history_edit = False
back = ''
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
    global back
    back = request.url
    global push_title
    global push_history_edit
    push_title = '|'
    push_history_edit = False
    title = push_title
    entry = query_db("SELECT * FROM entries WHERE title = ?", [title], one=True)
    if entry is not None:
        if not entry['current']:
            push_history_edit = True
        return render_template("wiki.html", entry=entry['text'], homepage=True)    
    elif 'username' in session and entry is None:
        return redirect(url_for('edit_homepage', title=title))
    else:
        return redirect(url_for('login_form'))

# individual wiki page
@app.route("/<title>")
def viewpage(title):
    global back
    back = request.url
    global push_title
    global push_history_edit
    push_title = title
    push_history_edit = False
    entry = query_db("SELECT * FROM entries WHERE title = ?", [title], one=True)
    if entry is not None:
        if not entry['current']:
            push_history_edit = True
        return render_template("wiki.html", entry=entry['text'])
    elif 'username' in session and entry is None:
        return redirect(url_for('editpage', title=title))
    else:
        return redirect(url_for('login_form'))


# edit handler just for no addon
@app.route('/_edit')
def edit_homepage():
    if 'username' in session:
        return render_template("edit.html", title='|')
    else:
        return redirect(url_for('login'))

# edit the wiki page
@app.route('/edit/<title>')
def editpage(title):
    if 'username' in session:
	   return render_template("edit.html", title=title)
    else:
        return redirect(url_for('login'))

# add the new entry from the editpage handler
@app.route('/add/<title>', methods=['POST'])
def add_entry(title):
    if 'username' in session:
        global versions
        versions[title] = 1
        current_date = get_datetime()
        db = get_db()
        db.execute('INSERT INTO entries (title, text, my_date, version, current) VALUES (?, ?, ?, ?, ?)',
                     [title, request.form['content'], current_date, versions[title], True])
        db.commit()
        #flash('New entry was successfully posted')
        if title == "|":
            return redirect(url_for('homepage'))
        return redirect(url_for('viewpage', title=title))
    else:
        return redirect(url_for('login'))


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
    db.execute('INSERT INTO entries (title, text, my_date, version, current) VALUES (?, ?, ?, ?, ?)',
                 [title + "v%s" % version, entry['text'], entry['my_date'], version, False])
    db.commit()
    # update entry
    db.execute('UPDATE entries SET text=?, my_date=?, version=?, current=? WHERE title=?', (request.form['content'], current_date, versions[title], True, title))
    db.commit()
    if title == "|":
        return redirect(url_for('homepage'))
    return redirect(url_for('viewpage', title=title))

@app.context_processor
def push_title():
    global push_title
    global push_history_edit
    return dict(title=push_title, history_edit=push_history_edit)

@app.context_processor
def get_user():
    if 'username' in session:
        user = session['username']
    else:
        user = ''
    return dict(user=user)

@app.context_processor
def utility_processor():
    def trunc_version(title):
        index = title.rfind('v')
        return title[:index]
    return dict(trunc_version=trunc_version)


"""
Primary History Functions
"""
@app.route("/_history")
def history_homepage():
    global back
    back = request.url
    global push_title
    global push_history_edit
    title = "|"
    push_title = title
    push_history_edit = False
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
        i -= 1
    # populate list
    for entry in entries:
        for version in history:
            if entry['title'] == version[0]:
                version.append(entry['text'])
                version.append(entry['version'])
                version.append(entry['my_date'])
    history_sorted = sorted(history, key=itemgetter(2), reverse=True)
    return render_template("history_index.html", history=history_sorted, title=title)
    
@app.route("/history/<title>")
def history(title):
    global back
    back = request.url
    global push_title
    global push_history_edit
    push_title = title
    push_history_edit = False
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
        i -= 1
    # populate list
    for entry in entries:
        for version in history:
            if entry['title'] == version[0]:
                version.append(entry['text'])
                version.append(entry['version'])
                version.append(entry['my_date'])
                version.append(entry['current'])
    history_sorted = sorted(history, key=itemgetter(2), reverse=True)
    return render_template("history_index.html", history=history_sorted, title=title)


@app.route("/history_update/<title>")
def history_update(title):
    if 'username' in session:
        entry = query_db("SELECT * FROM entries WHERE title = ?", [title], one=True)
        current_title = trunc_version(title)
        return render_template("edit.html", title=current_title, update=True, text=entry['text'])
    else:
        return redirect(url_for('login_form'))

"""
Sessions
"""
@app.route("/signup")
def signup():
    global back
    if 'username' in session:
        return redirect(back)
    else:
        return render_template('signup.html')

@app.route("/register", methods=['POST'])
def register():
    global back
    db = get_db()
    current_date = get_datetime()
    have_error = False
    username = request.form['username']
    password = request.form['password']
    verify = request.form['verify']
    user = query_db("SELECT * FROM users WHERE username = ?", [username], one=True)
    params = dict(username=username)

    if user:
        params['error_username'] = "That username is taken"
        have_error = True

    if not valid_username(username):
        params['error_username'] = "That's not a valid username."
        have_error = True

    if not valid_password(password):
        params['error_password'] = "That wasn't a valid password."
        have_error = True
    elif password != verify:
        params['error_verify'] = "Your passwords didn't match."
        have_error = True

    if have_error:
        return render_template('signup.html', **params)
    else:
        hpw = bcrypt.generate_password_hash(password)
        db.execute('INSERT INTO users (username, hpw, my_date) VALUES (?, ?, ?)',
                 [username, hpw, current_date])
        db.commit()
        session['username'] = username
        return redirect(back)

@app.route('/login_form')
def login_form():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    global back
    params = dict()
    username = request.form['username']
    password = request.form['password']
    user = query_db("SELECT * FROM users WHERE username = ?", [username], one=True)
    if user is None:
        params['error_username'] = "That username doesn't exist"
        return render_template('login.html', **params)
    if bcrypt.check_password_hash(user['hpw'], password):
        session['username'] = username
        return redirect(back)
    else:
        params['username'] = username
        params['error_password'] = "That's not the right password"
        return render_template('login.html', **params)


@app.route('/logout')
def logout():
    global back
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(back)

"""
Last thing to fix before deploying to server:
Fix edit from within history
"""

app.secret_key = secret()




if __name__ == '__main__':
    init_db()
    app.run(debug=True)#host='107.170.69.45'


"""
entry = query_db("SELECT * FROM users WHERE username = ?", [username], one=True)
temp = dict(username=entry['username'], hpw=entry['hpw'], my_date=entry['my_date'])
return render_template('test.html', **temp)#redirect(url_for('homepage'))
"""

# I really think that Michael sucks. He keeps trying to push all his website propaganda onto me. I don't want his propaganda. I am an independent thinker. And also a little drunk. I was just drinking margaritas at Copa. Happy Wednesday!