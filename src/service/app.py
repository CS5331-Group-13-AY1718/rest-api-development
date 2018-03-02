#!/usr/bin/python

from flask import Flask
from flask import g
from flask import request
from flask import render_template, flash, redirect, url_for, session, logging
from flask_cors import CORS
from datetime import datetime
import dateutil.parser
from wtforms import Form, StringField, TextAreaField, IntegerField, PasswordField, SelectField, validators
from passlib.hash import sha256_crypt
import json
import os
import sqlite3
import uuid
import pytz
from functools import wraps
from logging import FileHandler

DATABASE = 'database.db'

app = Flask(__name__)
# Enable cross origin sharing for all endpoints
CORS(app)

file_handler = FileHandler('log.txt')
app.logger.addHandler(file_handler)

def get_db():
    """UTILITY METHOD"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    """UTILITY METHOD"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """UTILITY METHOD"""
    cur = get_db().execute(query, args)
    get_db().commit()
    rv = cur.fetchall()
    cur.close()
    print(rv)
    return (rv if rv else None) if one else rv


def user_from_token(token):
    """UTILITY METHOD"""
    """Returns the corresponding user when given a token"""
    """IMPT: This returns a TWO-dimensional array, an array of users, where a user is an array of attributes"""
    query = "select * from users where token='%s'" % token
    user = query_db(query)
    """Since only one user should match the query at any time, select it"""
    return user[0]

def int_from_boolean(truth):
    """UTILITY METHOD"""
    if truth==True:
        return 1;
    else:
        return 0;

def get_current_datetime():
    """UTILITY METHOD"""
    """Using UTC+8 for singapore"""
    tz = pytz.timezone("Singapore")
    aware_dt = tz.localize(datetime.now())
    generatedDT = aware_dt.replace(microsecond=0).isoformat()
    return generatedDT

def make_diary_dict(row):
    """UTILITY METHOD"""
    """This method takes in a diary (1 sql row), which is an array of attributes"""
    """A diary = [id, title, author, publish_date, public, text]"""
    """Then converts it to a dictionary"""
    """Note that query_db returns a 2d array, or an array of rows"""
    time_from_ISO = dateutil.parser.parse(row[3])
    publish_date = time_from_ISO.date().strftime('%d/%m/%Y')
    publish_time = time_from_ISO.time().strftime('%I:%M%p')
    diaryDict = {"id":row[0],"title":row[1],"author":row[2],"publish_date":publish_date,"publish_time":publish_time,"public":row[4],"text":row[5]}
    return diaryDict

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            if session['logged_in']:
                user_token = user_from_token(session['token'])
                if session['username'] == user_token[0]:
                    return f(*args, **kwargs)
                else:
                    return redirect(url_for('users_authenticate'))
            else:
                return redirect(url_for('users_authenticate'))
        except KeyError:
            return redirect(url_for('users_authenticate'))
    return wrap

"""===========================================END OF UTILITY METHODS==========================================="""
"""===========================================START OF PYTHON (2.7) FLASK WEB APP==========================================="""

# Remember to update this list
ENDPOINT_LIST = ['/', '/meta/heartbeat', '/meta/members', '/users/register', '/users/authenticate', '/users/expire', '/user/logout', '/users', '/diary', '/public', '/diary/create', '/diary/delete', '/diary/permission']

def make_json_response(data, status=True, code=200, username=None, fullname=None, age=None):
    """Utility function to create the JSON responses."""

    to_serialize = {}
    if status:
        to_serialize['status'] = True
        if data is not None:
            to_serialize['result'] = data
        if username is not None:
            to_serialize['username'] = username
        if fullname is not None:
            to_serialize['fullname'] = fullname
        if age is not None:
            to_serialize['age'] = age
    else:
        to_serialize['status'] = False
        if data is not None:
            to_serialize['error'] = data
    response = app.response_class(
        response=json.dumps(to_serialize),
        status=code,
        mimetype='application/json'
    )
    return response


@app.route("/")
def index():
    """Returns a list of implemented endpoints."""
    return render_template('index.html')
    #make_json_response(ENDPOINT_LIST)


@app.route("/meta/heartbeat")
def meta_heartbeat():
    """Returns true"""
    return make_json_response(None)


@app.route("/meta/members")
def meta_members():
    """Returns a list of team members"""
    with open("./team_members.txt") as f:
        team_members = f.read().strip().split("\n")
    return make_json_response(team_members)

class RegisterForm(Form):
    fullname = StringField('Full name', [validators.Length(min=1, max=50)])
    age = IntegerField('Age', [validators.input_required()])
    username = StringField('Username', [validators.Length(min=4, max=20)])
    password = PasswordField('Password', [validators.DataRequired()])

@app.route("/users/register", methods=['GET', 'POST'])
def users_register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate:
        """Registers users"""
        """Registers users"""
        fullname = form.fullname.data
        age = form.age.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #paramsJSON = request.get_json()
        #username = paramsJSON['username']
        #password =  paramsJSON['password']
        #fullname = paramsJSON['fullname']
        #age = paramsJSON['age']
        try:
            query = "insert into users(username, password, fullname, age) values ('%s','%s','%s',%s)" % (username,password,fullname,str(age))
            result = query_db(query)
            return redirect(url_for('users_authenticate'))
            #make_json_response(None, code=201)
        except sqlite3.IntegrityError:
            result = "User already exists!"
            return make_json_response(result, status=False)
    else:
        return render_template('register.html', form=form)


@app.route("/users/authenticate", methods=['GET', 'POST'])
def users_authenticate():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        #paramsJSON = request.get_json()
        #username = paramsJSON['username']
        #password =  paramsJSON['password']

        """Check if such a user exists first"""
        query = "select password from users where username='%s'" % (username)
        result = query_db(query)

        if result == []:
            app.logger.info('%s failed to log in', username)
            return make_json_response(data=None, status=False)
        else:
            """Authenticates user"""
            password = result[0][0]
            if sha256_crypt.verify(password_candidate, password):
                """Query to insert token to users table token column"""
                generatedToken = uuid.uuid4()
                query = "update users SET token='%s' where username='%s'and password='%s'" % (str(generatedToken), username,password)
                result = query_db(query)

                session['logged_in'] = True
                session['username'] = username
                session['token'] = generatedToken

                app.logger.info('%s logged in successfully. token = %s', session['username'], session['token'])

                """An update query does not return a result in query_db()"""
                return redirect(url_for('index')) 
                #make_json_response(str(generatedToken))
            else:
                return render_template('login.html')
    else:
        return render_template('login.html')


@app.route("/users/expire", methods=['POST'])
def users_expire():
    if request.method == 'POST':
        """Authenticates users"""
        paramsJSON = request.get_json()
        token = paramsJSON['token']

        """Check if such a token exists first"""
        result = user_from_token(token)

        if result == []:
            return make_json_response(data=None, status=False)

        else:
            """De-authenticates user"""
            """Query to insert blank token to users table token column"""
            query = "update users SET token='%s' where token='%s'" % ("", token)
            result = query_db(query)
            """An update query does not return a result in query_db()"""
            return make_json_response(data=None)

@app.route('/users/logout')
@is_logged_in
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/users", methods=['GET', 'POST'])
def users_get():
    if request.method =='GET':
        """Returns all current usernames in DB, ONLY FOR DEBUGGING"""
        users = []
        for user in query_db('select * from users'):
            users.append(user)
        return make_json_response(users)

    if request.method =='POST':
        paramsJSON = request.get_json()
        token = paramsJSON['token']

        """Check if such a token exists first"""
        result = user_from_token(token)

        if result == []:
            return make_json_response(data="Invalid authentication token", status=False)

        else:
            return make_json_response(None, username=result[0], fullname=result[2], age=result[3])

@app.route("/public")
def public_get():
    """Retrieve all public diary entries"""
    """No req params needed, only response"""
    query = "select * from diaries where public='1'"
    result = query_db(query)
    arrOfDiaryDicts = []
    for row in result:
        arrOfDiaryDicts.append(make_diary_dict(row))
    return render_template('public.html', public=arrOfDiaryDicts)
    #make_json_response(arrOfDiaryDicts))

@app.route("/diary", methods=['GET', 'POST'])
@is_logged_in
def diary_get():
    #if request.method =='POST':
    """Retrieve all entries belonging to an authenticated user"""
    #paramsJSON = request.get_json()
    #token = paramsJSON['token']
    token = session['token']
    result = user_from_token(token)
    if result == []:
        return make_json_response(data="Invalid authentication token", status=False)
    else:
        username = result[0]
        query = "select * from diaries where author='%s'" % (username)
        result = query_db(query)
        arrOfDiaryDicts = []
        for row in result:
            arrOfDiaryDicts.append(make_diary_dict(row))
        return render_template('diary.html', diary=arrOfDiaryDicts)
        #make_json_response(arrOfDiaryDicts)

class DiaryForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    public = SelectField('Permission', choices=[('public', 'Public'), ('private', 'Private')])
    body = TextAreaField('Body', [validators.Length(min=1)])

@app.route("/diary/create", methods=['GET', 'POST'])
@is_logged_in
def diary_create():
    form = DiaryForm(request.form)
    if request.method =='POST' and form.validate:
        """Create a new diary entry"""
        title = form.title.data
        text = form.body.data
        public = form.public.data
        username = session['username']
        if public == 'public':
            public = True
        else:
            public = False

        #paramsJSON = request.get_json()
        #token = paramsJSON['token']
        #title = paramsJSON['title']
        #public = paramsJSON['public']
        #text = paramsJSON['text']
        #result = user_from_token(token)
        #if result ==[]:
        #    return make_json_response(data="Invalid authentication token", status=False)
        #else:
        #    username = result[0]
        generatedDT = get_current_datetime()
        query = "insert into diaries ('title', 'author', 'publish_date', 'public', 'text') values ('%s','%s','%s','%d','%s')" % (title,username,generatedDT,int_from_boolean(public),text)
        result = query_db(query)
        return redirect(url_for('diary_get'))
        #make_json_response(data=2, code=201)
    else:
        return render_template('diary_create.html', form=form)

@app.route("/diary/delete/<string:entryid>", methods=['POST'])
@is_logged_in
def diary_delete(entryid):
    if request.method =='POST':
        token = session['token']
        username = session['username']
        id = int(entryid)
        #paramsJSON = request.get_json()
        #token = paramsJSON['token']
        #id = paramsJSON['id']
        """Get user from token first"""
        user = user_from_token(token)
        """If no such user with this token exists, else"""
        if user == []:
            return make_json_response(data="Invalid authentication token", status=False)
        else:
            username = user[0]
            app.logger.info('Deleting diary id = %d from author = %s', id, username)
            query = "delete from diaries where author='%s' and id='%d'" % (username, id)
            result = query_db(query)
            return redirect(url_for('diary_get'))
            #return make_json_response(None)


@app.route("/diary/permission/<string:entryid>/<string:entrypublic>", methods=['POST'])
@is_logged_in
def diary_permission(entryid, entrypublic):
    if request.method =='POST':
        token = session['token']
        #paramsJSON = request.get_json()
        #token = paramsJSON['token']
        #id = paramsJSON['id']
        #public = int_from_boolean(paramsJSON['public'])

        """Get user from token first"""
        id = int(entryid)
        if entrypublic == "1":
            public = 0
        else:
            public = 1
        user = user_from_token(token)
        """If no such user with this token exists, else"""
        if user == []:
            return make_json_response(data="Invalid authentication token", status=False)
        else:
            username = user[0]
            query = "update diaries SET 'public'='%d' where id='%d'" % (public,id)
            result = query_db(query)        
            return redirect(url_for('diary_get'))
            #make_json_response(None)


if __name__ == '__main__':
    # Change the working directory to the script directory
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # Run the application
    app.secret_key='secret12345'
    app.run(debug=True, port=8080, host="0.0.0.0")
