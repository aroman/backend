import requests
from flask import Flask, request, render_template
import pprint as pp

VENMO_OAUTH_CLIENT_ID = "1601"
VENMO_OAUTH_CLIENT_SECRET = "kS6Xwrd9rzzkSd3C2BcjhJFMAxH3Kv3P"
VENMO_ACCESS_TOKEN = "eSN3Z3A2KeRbcnNTqgLu6mRA4K9uED9V"
VENMO_OAUTH_URL = "https://venmo.com/oauth/authorize?client_id=%s&scope=make_payments,access_profile,access_phone,access_friends,access_balance&response_type=code" % VENMO_OAUTH_CLIENT_ID

app = Flask(__name__)
app.debug = True

@app.route("/")
def index():
    return render_template('index.html',
            VENMO_OAUTH_URL=VENMO_OAUTH_URL)

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
            return "Error from Venmo OAUTH: %s" % error
        access_token = response_dict.get('access_token')

        user = response_dict.get('user')
        print "User from venmo oauth:"
        return pp.pformat(user)

    #     user_from_db = mongo.db.users.find_one({"venmo_id": user['id']})
    #     print "User from db:"
    #     pp(user_from_db)

    #     if user_from_db:
    #         print "User has used GrubHero before; we have them in the DB."
    #         user_from_db['access_token'] = access_token
    #         user_from_db['firstname'] = user['firstname']
    #         user_from_db['lastname'] = user['lastname']
    #         user_from_db['username'] = user['username']
    #         user_from_db['email'] = user['email']
    #         user_from_db['picture'] = user['picture']
    #         user_from_db['last_visit'] = datetime.utcnow()
    #         mongo.db.users.save(user_from_db)
    #     else:
    #         print "User has NOT used GrubHero before. Making account in DB."
    #         mongo.db.users.insert({
    #             "venmo_id": user['id'],
    #             "access_token": access_token,
    #             "firstname": user['firstname'],
    #             "lastname": user['lastname'],
    #             "username": user['username'],
    #             "email": user['email'],
    #             "picture": user['picture'],
    #             "last_visit": datetime.utcnow()
    #         })
    #         act_id = mongo.db.activities.insert({
    #             "type": "joined",
    #             "username": user['username'],
    #             "firstname": user['firstname'],
    #             "picture": user['picture'],
    #             "lastname": user['lastname'],
    #             "actor_venmo_id": user['id'],
    #             "when": datetime.utcnow()
    #         })
    #         print "THIS IS FROM SETUP"
    #         pp(mongo.db.activities.find_one(act_id)['when'])

    #     session['venmo_id'] = user['id']
    #     session['email'] = user['email']
    #     session['username'] = user['username']
    #     session['firstname'] = user['firstname']
    #     session['lastname'] = user['lastname']
    #     session['photo_url'] = user['picture']

    #     if 'return_url' in session and session['return_url']:
    #         url = session['return_url']
    #         session['return_url'] = None
    #         return redirect(url)
    #     else:
    #         return redirect(url_for('index'))
    else:
        return "Error"



if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80)