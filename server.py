import time
import json
import string
import random
import pusher
import datetime
import requests
import sendgrid
import funcy
from functools import wraps
from flask_oauth import OAuth
from pprint import pprint as pp
from flask.ext.pymongo import PyMongo
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, g
from bson.objectid import ObjectId

VENMO_OAUTH_CLIENT_ID = "1601"
VENMO_OAUTH_CLIENT_SECRET = "kS6Xwrd9rzzkSd3C2BcjhJFMAxH3Kv3P"
VENMO_ACCESS_TOKEN = "eSN3Z3A2KeRbcnNTqgLu6mRA4K9uED9V"
VENMO_OAUTH_URL = "https://venmo.com/oauth/authorize?client_id=%s&scope=make_payments,access_profile,access_phone,access_friends,access_balance&response_type=code" % VENMO_OAUTH_CLIENT_ID

TWITTER_OAUTH_URL = "https://api.twitter.com/oauth/authorize"


MATCHMAKING_TIMEOUT = 5 # seconds

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb://ludacris:moneymaker@ds033499.mongolab.com:33499/betson"
app.secret_key = 'zgzQQCCn50mDwScfOyQ9'
app.debug = True
mongo = PyMongo(app)
# oauth = OAuth()

# twitter = oauth.remote_app('twitter',
#     base_url='https://api.twitter.com/1/',
#     request_token_url='https://api.twitter.com/oauth/request_token',
#     access_token_url='https://api.twitter.com/oauth/access_token',
#     authorize_url='https://api.twitter.com/oauth/authenticate',
#     consumer_key='7DEWbqXHmfrZGz9LMtIIgA',
#     consumer_secret='1Qt315xblwCCDbsSWRN2jaYCZzzsM6wACZrtPTyXWs'
# )
# 
# request_token, request_token_secret = twitter.get_request_token()
# authorize_url = twitter.get_authorize_url(request_token)

p = pusher.Pusher(
  app_id='66156',
  key='e4bab17358b4582eb567',
  secret='e5e8da723ba71f683933'
)

# @app.route("/setup")
# def setup():
#     oauth_code = request.args.get('code')
#     if oauth_code:
#         url = "https://api.venmo.com/oauth/access_token"
#         data = {
#             "client_id": VENMO_OAUTH_CLIENT_ID,
#             "client_secret": VENMO_OAUTH_CLIENT_SECRET,
#             "code": oauth_code
#         }

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

def tweet(message, other_person, tweet, twitter):
    body = "I just challenged @" + other_person + " to see " + message# + " at @PennApps #BetsOn"
    # url = "https://api.twitter.com/1/statuses/update.json"
    data = {"status" : body}
    resp = twitter.post('statuses/update.json', data=data)
    if resp.status == 403:
        print 'Your tweet was too long.'
    elif resp.status == 401:
        print 'Authorization error with Twitter.'
    else:
        print 'Successfully tweeted your tweet (ID: #%s)' % resp.data['id']
        return True
    return False

def send_email(txt, to):
    pass
    # s = sendgrid.Sendgrid('jzone3', 'beta-code', secure=True)
    # s = sendgrid.Sendgrid('betson', 'betsonbetsoff1', secure=True)
    # message = sendgrid.Message(("info@betsonapp.com", "BetsOn Team"), "Your new bet!", txt)
    # message.add_to(to)
    # s.web.send(message)

@app.route("/")
def index():
    pp(session)
    if logged_in():
        user_from_db = mongo.db.users.find_one(session['venmo_id'])
        if user_from_db['pair_token']:
            return render_template('connect.html',
                    logged_in=False,
                    pair_token=user_from_db['pair_token'],
                    VENMO_OAUTH_URL=VENMO_OAUTH_URL)
        else:
            return render_template('homepage.html',
                    logged_in=True,
                    VENMO_OAUTH_URL=VENMO_OAUTH_URL)

    return render_template('index.html',
            logged_in=False,
            VENMO_OAUTH_URL=VENMO_OAUTH_URL)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

shakes_in_progress = []

def remove_duplicates(lst):
    already_in = {}
    new = []
    for i in lst:
        try:
            already_in[i]
        except KeyError:
            new.append(i)
            already_in[i] = 5
    return new

def find_site(name):
    links = []
    good_links = []
    url = "http://google.com/search?q=" + str(name)
    r = requests.get(url=url)

    res = r.text
    res_list = res.split("&amp;")
    for link in res_list:
        if 'href="/url?q=' in link:
            link = link.split('href="/url?q=')[1]
            if 'googleusercontent' not in link:
                links.append(link)
    for link in links:
        if not (link[-1:] == "/" and link.count("/") > 3) and not (link[-1:] != "/" and link.count("/") > 2):
            good_links.append(link)

    return remove_duplicates(good_links)

def is_in(site, item):
    item = item.lower()
    url = find_site(site)[0]
    x = requests.get(url).text.lower()
    if not ">" + item + "<" in x and not " " + item + " " in x:
        try:
            print x
        except:
            pass
        return False
    parts = x.split(" " + item + " ")
    if len(parts) < 2:
        parts = x.split(">" + item + "<")
        if len(parts) < 2:
            return False
    first = parts[0].split(" ")[-1]
    if ">" in first:
        first = first.split(">")[-1]
    elif '"' in first:
        first = first.split('"')[-1]
    second = parts[1].split(" ")[0]
    if "<" in second:
        second = second.split("<")[0]
    elif '"' in second:
        second = second.split('"')[-1]
    to_return = first + " " + item + " " + second
    to_return = to_return.replace("&nbsp;", " ")
    to_return = to_return.strip()
    if to_return[-1] == ">" or to_return[-1] == "<":
        to_return = to_return[:-1]
    if to_return[-1] == '"' or to_return[-1] == "'":
        to_return = to_return[:-1]
    if to_return[0] == ">" or to_return[0] == "<":
        to_return = to_return[1:]
    if to_return[0] == '"' or to_return[0] == "'":
        to_return = to_return[1:]
    return to_return

def actually_create_bet(bet_object):
    print "In actually_create_bet!"
    pp(bet_object)
    proposer_from_db = mongo.db.users.find_one({"pebble_token": bet_object['proposer_token']})
    accepter_from_db = mongo.db.users.find_one({"pebble_token": bet_object['accepter_token']})
    bet_info = mongo.db.user_bets.find_one({"_id": ObjectId(bet_object["bet_id"])})
    print "BET INFO!!!"
    pp(bet_info)
    pp(proposer_from_db)
    pp(accepter_from_db)
    if bet_object['bet_id'] == 100:
        # Hard code: proposer wins
        actual_charge = -bet_object['bet_amount']
        venmo_note = "%s won a bet with %s!" % (proposer_from_db['firstname'], accepter_from_db['firstname'])
        proposer_won = True
    elif bet_object['bet_id'] == 200:
        # Hard code: proposer loses
        actual_charge = bet_object['bet_amount']
        venmo_note = "%s lost a bet with %s!" % (accepter_from_db['firstname'], proposer_from_db['firstname'])
        proposer_won = False
    elif bet_info['kind'] == 'grepurl':
        if is_in(bet_info['url'], bet_info['string']):
            actual_charge = -bet_object['bet_amount']
            venmo_note = "%s won a bet with %s!" % (proposer_from_db['firstname'], accepter_from_db['firstname'])
            proposer_won = True
        else:
            actual_charge = bet_object['bet_amount']
            venmo_note = "%s lost a bet with %s!" % (accepter_from_db['firstname'], proposer_from_db['firstname'])
            proposer_won = False
    else:
        err = "ERROR: Unknown bet ID!"
        pp(err)
        return err
    mongo_res = mongo.db.bets.insert({
        "proposer": proposer_from_db['_id'],
        "accepter": accepter_from_db['_id'],
        "amount": bet_object['bet_amount'],
        "timestamp": bet_object['timestamp'],
        "proposer_won": proposer_won 
    })
    pp(mongo_res)
    url = "https://api.venmo.com/payments"
    data = {
        "access_token": proposer_from_db['access_token'],
        "user_id": accepter_from_db['_id'],
        "note": "%s @ %s (via BetsOn)" % (venmo_note, str(datetime.datetime.now())),
        "amount": actual_charge 
    }
    pp(data)
    response = requests.post(url, data)
    pp(response.json())
    return "OK" 

@app.route("/shake/<bet_id>", methods=['POST'])
def shake_propose(bet_id):
    pebble_token = request.form['pebble_token']
    bet_amount = int(request.form['bet_amount'])
    now = datetime.datetime.utcnow()

    already_in = False
    for shake in shakes_in_progress:
        if 'proposer_token' in shake:
            already_in = shake['proposer_token'] == pebble_token
            shake['propose_time'] = now
        if 'accept_time' in shake:
            delta = (now - shake['accept_time']).seconds
            if delta < MATCHMAKING_TIMEOUT:
                actually_create_bet({
                    "bet_id": bet_id,
                    "bet_amount": bet_amount,
                    "timestamp": now,
                    "proposer_token": pebble_token,
                    "accepter_token": shake['accepter_token'],
                })
                shakes_in_progress.remove(shake)
                # tweet("who has more twitter followers", "personsTwitter")
                print "WE'VE GOT A MATCH!!!!!!!!!"
                return "WE'VE GOT A MATCH!!!!!"
    if already_in:
        return "Already advertised, updated timestamp"
    else:
        to_append = {
            "proposer_token": pebble_token,
            "bet_amount": bet_amount,
            "bet_id": bet_id,
            "propose_time": now 
        }
        shakes_in_progress.append(to_append)
        return "Not listed; advertised"

    pp(shakes_in_progress)

@app.route("/shake", methods=['POST'])
def shake_accept():
    pebble_token = request.form['pebble_token']
    now = datetime.datetime.utcnow()

    already_in = False
    for shake in shakes_in_progress:
        if 'accepter_token' in shake:
            already_in = shake['accepter_token'] == pebble_token
            shake['accept_time'] = now
        if 'propose_time' in shake:
            delta = (now - shake['propose_time']).seconds
            if delta < MATCHMAKING_TIMEOUT:
                actually_create_bet({
                    "bet_id": shake['bet_id'],
                    "bet_amount": shake['bet_amount'],
                    "timestamp": now,
                    "proposer_token": shake['proposer_token'],
                    "accepter_token": pebble_token,
                })
                shakes_in_progress.remove(shake)
                # tweet("who has more twitter followers", "personsTwitter")
                print "WE'VE GOT A MATCH!!!!!!!!!"
                return "WE'VE GOT A MATCH!!!!!"
    if already_in:
        print "Already advertised, updated timestamp"
    else:
        to_append = {
            "accepter_token": pebble_token,
            "accept_time": now 
        }
        shakes_in_progress.append(to_append)
        return "Not listed; advertised"
    pp(shakes_in_progress)

@app.route("/pair/<pair_token>", methods=['POST'])
def pair(pair_token):
    pp(shakes_in_progress)
    pp(request.form)
    pebble_token = request.form['pebble_token']
    p[pair_token].trigger('success', {'message': 'PAIRED w/ %s' % pebble_token })
    r = mongo.db.users.update({"pair_token": pair_token}, { "$set": { "pair_token": False, "pebble_token": pebble_token } })
    if r['updatedExisting'] == True:
        return "success"
    else:
        return "failed; token expired, invalid or already paired"

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
                "pair_token": ''.join(random.choice(string.digits) for x in range(6)),
                "email": user_from_oauth['email'],
                "picture": user_from_oauth['picture']
            })
            send_email("Welcome to BetsOn!\n- The BetsOn Team", user_from_oauth['email'])

        session['venmo_id'] = user_from_oauth['id']
        session['email'] = user_from_oauth['email']
        session['username'] = user_from_oauth['username']
        session['firstname'] = user_from_oauth['firstname']
        session['lastname'] = user_from_oauth['lastname']
        session['avatar_url'] = user_from_oauth['picture']

        return redirect(url_for('index'))
    else:
        return "Error"

@app.route("/bets", methods=['GET', 'POST'])
def bets():
    pebble_token = request.form['pebble_token']

    user_from_db = mongo.db.users.find_one({"pebble_token": pebble_token})
    users_bets = mongo.db.user_bets.find({ "creator": user_from_db['_id'] })
    pp(user_from_db)

    da_bets = []
    for user_bet in users_bets:
        da_bets.append({
            "label": user_bet['label'],
            "description": user_bet['kind'],
            "id": str(user_bet['_id'])
        })
    pp(da_bets)
    bets_data = [{"label": "propwin", "id": 100, "description": "Proposer will always win!"},
    {"label": "proplose", "id": 200, "description": "Proposer will always win!"}]

    return jsonify(bets=da_bets)

@app.route("/win", methods=['GET'])
def win():
    url = "https://api.venmo.com/payments"
    data = {
        "access_token": hero['access_token'],
        "user_id": participant['venmo_id'],
        "note": "%s (via GrubHero)" % meal['name'],
        "amount": -total
    }
    pp(data)
    response = requests.post(url, data)
    pp(response.json())

@app.route("/bets/new", methods=['GET', 'POST'])
@login_required
def new_bet():
    pp(request.form)
    if request.method == 'POST':
        if request.form['platform'] == 'custom':
            if request.form['time'] == 'now':
                mongo_res = mongo.db.user_bets.insert({
                    "creator": session['venmo_id'],
                    "kind": "grepurl",
                    "url": request.form['url'],
                    "label": request.form['name'],
                    "string": request.form['string']
                })
                # mongo_res = mongo.db.users.update({"_id": session['venmo_id']}, {"$push": { "created_bets": to_append }})
                pp(mongo_res)

        return "Ok"
    else:
        return render_template('new_bet.html',
                logged_in=logged_in())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)