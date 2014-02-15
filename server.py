import json
import string
import random
import pusher
import requests
from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, g
from flask.ext.pymongo import PyMongo
from pprint import pprint as pp
from pprint import pformat

VENMO_OAUTH_CLIENT_ID = "1601"
VENMO_OAUTH_CLIENT_SECRET = "kS6Xwrd9rzzkSd3C2BcjhJFMAxH3Kv3P"
VENMO_ACCESS_TOKEN = "eSN3Z3A2KeRbcnNTqgLu6mRA4K9uED9V"
VENMO_OAUTH_URL = "https://venmo.com/oauth/authorize?client_id=%s&scope=make_payments,access_profile,access_phone,access_friends,access_balance&response_type=code" % VENMO_OAUTH_CLIENT_ID

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb://ludacris:moneymaker@ds033499.mongolab.com:33499/betson"
app.secret_key = 'zgzQQCCn50mDwScfOyQ9'
app.debug = True
mongo = PyMongo(app)

p = pusher.Pusher(
  app_id='66156',
  key='e4bab17358b4582eb567',
  secret='e5e8da723ba71f683933'
)

def logged_in():
    return ("venmo_id" in session) and mongo.db.users.find_one(session['venmo_id'])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "venmo_id" not in session:
            return redirect(url_for('login', next=request.url))
        else:
            g.user = mongo.db.users.find_one(session['venmo_id'])
            return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    pp(session)
    if logged_in():
        user_from_db = mongo.db.users.find_one(session['venmo_id'])
        return render_template('index.html',
                logged_in=True,
                pair_token=user_from_db['pair_token'],
                VENMO_OAUTH_URL=VENMO_OAUTH_URL)

    return render_template('index.html',
            logged_in=False,
            VENMO_OAUTH_URL=VENMO_OAUTH_URL)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/shake", methods=['POST'])
@login_required
def shake():
    pp(request.form)
    mongo.db.bets.insert({
        'challenger_token': request.form.pebble_token,
    })
    return "OK for now"

@app.route("/pair/<pair_token>", methods=['POST'])
def pair(pair_token):
    pp(request.form)
    pebble_token = request.form['pebble_token']
    p[pair_token].trigger('success', {'message': 'PAIRED w/ %s' % pebble_token })
    r = mongo.db.users.update({"pair_token": pair_token}, { "$set": { "pair_token": False, "pebble_token": pebble_token } })
    if r['updatedExisting'] == True:
        return "success"
    else:
        return "failed; invalid or expired token"

    return "Success"

@app.route("/setup")
def setup():
    oauth_code = request.args.get('code')
    if oauth_code:
        url = "https://api.venmo.com/oauth/access_token"
        data = {
            "client_id": VENMO_OAUTH_CLIENT_ID,
            "client_secret": VENMO_OAUTH_CLIENT_SECRET,
            "code": oauth_code
        }
        response = requests.post(url, data)
        response_dict = response.json()
        error = response_dict.get('error')
        if error:
            if error['code'] == 257: # Access code already used
                print "Venmo OAUTH token already used, redirecting to index"
                return redirect(url_for('index'))
            else:
                return "Venmo OAUTH request returned an unexpected error: %s" % error
        access_token = response_dict.get('access_token')

        user_from_oauth = response_dict.get('user')
        user_from_db = mongo.db.users.find_one(user_from_oauth['id'])

        if user_from_db:
            print "User has used BetsOn before; we have them in the DB."
            user_from_db['access_token'] = access_token
            user_from_db['firstname'] = user_from_oauth['firstname']
            user_from_db['lastname'] = user_from_oauth['lastname']
            user_from_db['username'] = user_from_oauth['username']
            user_from_db['email'] = user_from_oauth['email']
            user_from_db['picture'] = user_from_oauth['picture']
            user_from_db['_id'] = user_from_oauth['id']
            mongo.db.users.save(user_from_db)
        else:
            print "User has NOT used BetsOn before. Making account in DB."
            mongo.db.users.insert({
                "_id": user_from_oauth['id'],
                "access_token": access_token,
                "firstname": user_from_oauth['firstname'],
                "lastname": user_from_oauth['lastname'],
                "username": user_from_oauth['username'],
                "pair_token": ''.join(random.choice(string.ascii_lowercase) for x in range(6)),
                "email": user_from_oauth['email'],
                "picture": user_from_oauth['picture']
            })

        session['venmo_id'] = user_from_oauth['id']
        session['email'] = user_from_oauth['email']
        session['username'] = user_from_oauth['username']
        session['firstname'] = user_from_oauth['firstname']
        session['lastname'] = user_from_oauth['lastname']
        session['avatar_url'] = user_from_oauth['picture']

        return redirect(url_for('index'))
    else:
        return "Error"


@app.route("/bets", methods=['GET'])
@login_required
def bets():
    bets_data = [{"title": "twitter", "subtitle": "My most recent Facebook post will get more likes!"}]
    return jsonify(bets=bets_data)

@app.route("/bets/new", methods=['GET', 'POST'])
@login_required
def new_bet():
    pp(request.form)
    return render_template('new_bet.html',
            logged_in=logged_in(),
            VENMO_OAUTH_URL=VENMO_OAUTH_URL)
    # mongo.db.bets.insert({
        # ''    
    # })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)