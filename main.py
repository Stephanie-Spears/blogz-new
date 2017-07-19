import os
from flask import Flask, request, redirect, render_template, session, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz-new:root@localhost:8889/blogz-new'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = 'f8wv3w2f>v9j4sEuhcNYydAGMzzZJgkGgyHE9gUqaJcCk^f*^o7fQyBTXtTvcYM'



class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(480))
    created = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __init__(self, title, body, owner): #created = None
        self.title = title
        self.body = body
        # if created is None:
        #     created = datetime.utcnow()
        self.created = datetime.utcnow()
        self.owner = owner

    def __repr__ (self):
        return '<\nID: %s\nTitle: %s\nBody: %s\nPub Date: %s\nEntries: %s\n>' % (self.id, self.title, self.body, self.created, self.owner)

    def is_valid(self):
        if self.title and self.body and self.created:
            return True
        else:
            return False


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    entries = db.relationship('Entry', backref='owner')
    def __init__(self, email, password): #entries = None
        self.email = email
        self.password = password

    def __repr__ (self):
        return '<\nID: %s\nEmail: %s\n>' % (self.id, self.email) #self.password, elf.entries

    def is_valid(self):
        if self.email and self.password:
            return True
        else:
            return False


# 
# @app.route('/search_by_owner', methods=['POST'])
# def search_by_owner():
    # user_entry = User.query.filter_by(email=email).first()

    # entry.owner = request.form['entry_owner']
    # entry_posters_list = User.query.all()
    #
    # if entry_owner and (entry.owner in entry_posters_list): ##
    #     return render_template('/serach_by_owner.html', entry_owner=entry_owner)
    # else:
    #     flash('User not found or has no posts')
    #     return render_template('/all_entries.html')

@app.before_request
def require_login():
    allowed_routes = ['login', 'register']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['email'] = email
            flash("Logged in")
            print(session)
            return redirect('/')
        else:
            flash('User password incorrect, or user does not exist', 'error')

    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        if not email or not password or not verify or (password != verify):
            if not email:
                flash('Please enter a valid email')
            if not password:
                flash('Please enter a valid password')
            if password != verify:
                flash('Passwords do not match')
            return render_template('register.html', email=email)

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/')
        else:
            # TODO - user better response messaging
            return "<h1>Duplicate user</h1>"

    return render_template('register.html')



#
@app.route("/blog")
def display_blog_entries():
    '''
    Either list one entry with the given ID
    Or list all blog entries (in default or newest order)
    '''
    # TODO refactor to use routes with variables instead of GET parameters
    entry_id = request.args.get('id')
    if (entry_id):
        entry = Entry.query.get(entry_id)
        return render_template('single_entry.html', title="Blog Entry", entry=entry)

    # if we're here, we need to display all the entries
    # TODO store sort direction in session[] so we remember user's preference
    sort = request.args.get('sort')
    if (sort=="newest"):
        all_entries = Entry.query.order_by(Entry.created.desc()).all()
    else:
        all_entries = Entry.query.all()
    return render_template('all_entries.html', title="All Entries", all_entries=all_entries)




#
@app.route('/new_entry', methods=['GET', 'POST'])
def new_entry():
    '''
    GET: Display form for new blog entry
    POST: create new entry or redisplay form if values are invalid
    '''
    owner = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        new_entry_title = request.form['title']
        new_entry_body = request.form['body']
        # new_entry_owner = request.form['owner']
        new_entry_owner = owner #can replace with owner = User.query.filter_by(email=session['email']).first()
        new_entry = Entry(new_entry_title, new_entry_body, new_entry_owner)

        if new_entry.is_valid():
            db.session.add(new_entry)
            db.session.commit()

            # display just this most recent blog entry
            url = "/blog?id=" + str(new_entry.id)
            return redirect(url)
        else:
            flash("Please check your entry for errors. Both a title and a body are required.")
            return render_template('new_entry_form.html',
                title="Create new blog entry",
                new_entry_title=new_entry_title,
                new_entry_body=new_entry_body, new_entry_owner=new_entry_owner)

    else: # GET request
        return render_template('new_entry_form.html', title="Create new blog entry")


@app.route('/')
def index():
    # owner = User.query.filter_by(email=session['email']).first()
    return redirect('/blog')

#to render changes to css etc. in real time, instead of relying on possibly old, outdated caches
""" Inspired by http://flask.pocoo.org/snippets/40/ """
@app.url_defaults
def hashed_url_for_static_file(endpoint, values):
    if 'static' == endpoint or endpoint.endswith('.static'):
        filename = values.get('filename')
        if filename:
            if '.' in endpoint:  # has higher priority
                blueprint = endpoint.rsplit('.', 1)[0]
            else:
                blueprint = request.blueprint  # can be None too

            if blueprint:
                static_folder = app.blueprints[blueprint].static_folder
            else:
                static_folder = app.static_folder

            param_name = 'h'
            while param_name in values:
                param_name = '_' + param_name
            values[param_name] = static_file_hash(os.path.join(static_folder, filename))

def static_file_hash(filename):
  return int(os.stat(filename).st_mtime) # or app.config['last_build_timestamp'] or md5(filename) or etc...

#
if __name__ == '__main__':
    app.run()
