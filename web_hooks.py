from flask import Flask, request, abort
import hmac
import hashlib
import base64
import ssl
import shopify
from shopify_practise import change_status
import os
import json
import re

app = Flask(__name__)

SECRET = bytes(change_status().creds.get("SECRET"),'utf-8')
end_file = os.getcwd()+"/staging.json"

def verify_webhook(data, hmac_header ):
    digest = hmac.new(SECRET, data , hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))



@app.route('/eight/webhook/product_update', methods=['POST'])
def handle_webhook():
    data = request.get_data()
    verified = verify_webhook(data, request.headers.get('X-Shopify-Hmac-SHA256'))

    if not verified:
        abort(401)

    data = json.loads(data.decode('utf-8'))
    with open(end_file,"w") as f: json.dump(data,f,indent=1)
    return data,200

def sanitize_string(searchTerm:str) ->str:
    new_key = "".join(filter(str.isalpha,searchTerm))
    return new_key if new_key else searchTerm

def clean_d():
    with open(end_file,"r") as f: data = json.load(f)
    return data

if __name__ == "__main__":
    app.run(debug=True)
