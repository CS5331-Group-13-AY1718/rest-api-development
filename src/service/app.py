#!/usr/bin/python

from flask import Flask
from flask import g
from flask import request
from flask_cors import CORS
from datetime import datetime
import json
import os
import sqlite3
import uuid
import pytz

DATABASE = 'database.db'


app = Flask(__name__)
# Enable cross origin sharing for all endpoints
CORS(app)

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
    if user != []:
	return user[0]
    else:
        return user

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
    diaryDict = {"id":row[0],"title":row[1],"author":row[2],"publish_date":row[3],"public":row[4],"text":row[5]}
    return diaryDict

"""===========================================END OF UTILITY METHODS==========================================="""
"""===========================================START OF PYTHON (2.7) FLASK WEB APP==========================================="""

# Remember to update this list
ENDPOINT_LIST = ['/', '/meta/heartbeat', '/meta/members', '/users/register', '/users/authenticate', '/users/expire', '/users', '/diary', '/diary/create', '/diary/delete', '/diary/permission']

def make_json_response(data, status=True, code=200):
    """Utility function to create the JSON responses."""

    to_serialize = {}
    if status:
        to_serialize['status'] = True
        if data is not None:
            to_serialize['result'] = data
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
    return make_json_response(ENDPOINT_LIST)


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


@app.route("/users/register", methods=['POST'])
def users_register():
    if request.method == 'POST':
        """Registers users"""
        paramsJSON = request.get_json()
        username = paramsJSON['username']
        password =  paramsJSON['password']
        fullname = paramsJSON['fullname']
        age = paramsJSON['age']
        try:
            query = "insert into users(username, password, fullname, age) values ('%s','%s','%s',%s)" % (username,password,fullname,str(age))
            result = query_db(query)
            return make_json_response(None, code=201)
        except sqlite3.IntegrityError:
            result = "User already exists!"
            return make_json_response(result, status=False)


@app.route("/users/authenticate", methods=['POST'])
def users_authenticate():
    if request.method == 'POST':
        paramsJSON = request.get_json()
        username = paramsJSON['username']
        password =  paramsJSON['password']

        """Check if such a user exists first"""
        query = "select * from users where username='%s'" % (username)
        result = query_db(query)

        if result == []:
            return make_json_response(data=None, status=False)

        else:
            """Authenticates user"""
            """Query to insert token to users table token column"""
            generatedToken = uuid.uuid4()
            query = "update users SET token='%s' where username='%s'and password='%s'" % (str(generatedToken), username,password)
            result = query_db(query)
            """An update query does not return a result in query_db()"""
            return make_json_response(data={"token":str(generatedToken)})


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
            query = "update users SET token=%s where token='%s'" % ("NULL", token)
            result = query_db(query)
            """An update query does not return a result in query_db()"""
            return make_json_response(data=None)


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
            return make_json_response(data={"username":result[0], "fullname":result[2], "age":result[3]})



@app.route("/diary", methods=['GET', 'POST'])
def diary_get():
    if request.method =='GET':
        """Retrieve all public diary entries"""
        """No req params needed, only response"""
        query = "select * from diaries where public='1'"
        result = query_db(query)
        arrOfDiaryDicts = []
        for row in result:
            arrOfDiaryDicts.append(make_diary_dict(row))
        return make_json_response(arrOfDiaryDicts)

    if request.method =='POST':
        """Retrieve all entries belonging to an authenticated user"""
        paramsJSON = request.get_json()
        token = paramsJSON['token']
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
            return make_json_response(arrOfDiaryDicts)


@app.route("/diary/create", methods=['POST'])
def diary_create():
    if request.method =='POST':
        """Create a new diary entry"""
        paramsJSON = request.get_json()
        token = paramsJSON['token']
        title = paramsJSON['title']
        public = paramsJSON['public']
        text = paramsJSON['text']
        result = user_from_token(token)
        if result ==[]:
            return make_json_response(data="Invalid authentication token", status=False)
        else:
            username = result[0]
            generatedDT = get_current_datetime()
            query = "insert into diaries ('title', 'author', 'publish_date', 'public', 'text') values ('%s','%s','%s','%d','%s')" % (title,username,generatedDT,int_from_boolean(public),text)
            result = query_db(query)

            """Retrieve last inserted id"""
            query = "select seq from sqlite_sequence where name='diaries'" 
            result = query_db(query)
            return make_json_response(data={"id":result[0][0]}, code=201)


@app.route("/diary/delete", methods=['POST'])
def diary_delete():
    if request.method =='POST':
        paramsJSON = request.get_json()
        token = paramsJSON['token']
        id = paramsJSON['id']
        """Get user from token first"""
        user = user_from_token(token)
        """If no such user with this token exists, else"""
        if user == []:
            return make_json_response(data="Invalid authentication token", status=False)
        else:
            username = user[0]
            query = "delete from diaries where author='%s' and id='%d'" % (username, id)
            result = query_db(query)
            return make_json_response(None)


@app.route("/diary/permission", methods=['POST'])
def diary_permission():
    if request.method =='POST':
        paramsJSON = request.get_json()
        token = paramsJSON['token']
        id = paramsJSON['id']
        public = int_from_boolean(paramsJSON['public'])

        """Get user from token first"""
        user = user_from_token(token)
        """If no such user with this token exists, else"""
        if user == []:
            return make_json_response(data="Invalid authentication token", status=False)
        else:
            username = user[0]
            query = "update diaries SET 'public'='%d' where id='%d'" % (public,id)
            result = query_db(query)        
            return make_json_response(None)


if __name__ == '__main__':
    # Change the working directory to the script directory
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # Run the application
    app.run(debug=False, port=8080, host="0.0.0.0")
