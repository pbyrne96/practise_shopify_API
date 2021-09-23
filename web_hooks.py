from flask import Flask, request, abort
import hmac
import hashlib
import base64
import shopify
from shopify_practise import change_status
import os
import json
import re

app = Flask(__name__)

access = change_status().creds
SECRET = bytes(access.get("SECRET"),'utf-8')
HMAC_STR = 'X-Shopify-Hmac-SHA256'

shop_url = access.get("url")
product_update_file = os.getcwd()+"/staging.json"
order_update_file = os.getcwd()+"/order_update.json"
customer_records_file = os.getcwd() + "/customer_records.json"

cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
verify_token = lambda data, r: verify_webhook(data,r.headers.get(HMAC_STR))
clean_data = lambda data : json.loads(data.decode('utf-8'))

msg = ("Webhook received.",200)

def verify_webhook(data, hmac_header ):
    digest = hmac.new(SECRET, data , hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))

@app.route('/eight/webhook/product_update', methods=['GET','POST'])
def handle_webhook():
    data = request.get_data()
    verified = verify_token(data,request)

    if not verified:
        abort(401)

    data = clean_data(data)
    data['id'] = int(data.get('id'))
    data['body_html'] = "".join(i if ord(i) < 128 else '' for i in re.sub(cleanr,'',data.get('body_html')))\
                                                                if data['body_html'] else data['body_html']

    with open(product_update_file,"w") as f: json.dump(data,f,indent=1)
    return msg

@app.route('/eight/webhook/order_update',methods=['GET','POST'])
def order_update():
    data = request.get_data()
    
    verified = verify_token(data,request)
    if verified:
        abort(401)
    data = clean_data(data)
    print(data)
    return msg
    
if __name__ == "__main__":
    app.run(debug=True)
 
      
