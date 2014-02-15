import requests
import json

BASE_URL = "http://betsonapp.com/"

if __name__ == '__main__':
    payload = {
        'pebble_token': "7e2tCmSOEWeMkCmQxERpqyaJV"
    }
    print json.dumps(payload)
    r = requests.post(BASE_URL + "shake", data=payload)