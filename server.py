import requests
import funcy as f
from flask import Flask, request, render_template, redirect, url_for, session
from flask.ext.pymongo import PyMongo
from pprint import pprint as pp

VENMO_OAUTH_CLIENT_ID = "1601"
VENMO_OAUTH_CLIENT_SECRET = "kS6Xwrd9rzzkSd3C2BcjhJFMAxH3Kv3P"
VENMO_ACCESS_TOKEN = "eSN3Z3A2KeRbcnNTqgLu6mRA4K9uED9V"
VENMO_OAUTH_URL = "https://venmo.com/oauth/authorize?client_id=%s&scope=make_payments,access_profile,access_phone,access_friends,access_balance&response_type=code" % VENMO_OAUTH_CLIENT_ID

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb://ludacris:moneymaker@ds033499.mongolab.com:33499/betson"
app.secret_key = 'zgzQQCCn50mDwScfOyQ9'
app.debug = True
mongo = PyMongo(app)

def logged_in():
    return "venmo_id" in session

@app.route("/")
def index():
    return render_template('index.html',
            logged_in=logged_in(),
            VENMO_OAUTH_URL=VENMO_OAUTH_URL)

@app.route("/logout")
def logout():
    session.pop('venmo_id', None)
    return redirect(url_for('index'))

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
        user_from_db = mongo.db.users.find_one(user['id'])

        if user_from_db:
            print "User has used BetsOn before; we have them in the DB."
            user_from_db = dict(user)
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
                "_id": user['id'],
                "access_token": access_token,
                "firstname": user_from_oauth['firstname'],
                "lastname": user_from_oauth['lastname'],
                "username": user_from_oauth['username'],
                "email": user_from_oauth['email'],
                "picture": user_from_oauth['picture']
            })

        session['venmo_id'] = user_from_oauth['id']
        session['email'] = user_from_oauth['email']
        session['username'] = user_from_oauth['username']
        session['firstname'] = user_from_oauth['firstname']
        session['lastname'] = user_from_oauth['lastname']
        session['avatar_url'] = user_from_oauth['picture']

        if 'return_url' in session and session['return_url']:
            url = session['return_url']
            session['return_url'] = None
            return redirect(url)
        else:
            return redirect(url_for('index'))
    else:
        return "Error"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)