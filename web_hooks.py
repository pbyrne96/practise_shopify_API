from flask import Flask, request, abort
import hmac
import hashlib
import base64
from shopify_practise import change_status
import os
import json
import re
import os
# import shopify

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

msg = "Webhook received.",200

def submit_file(file_to_submit,data):
    with open(file_to_submit,"w") as f: json.dump(data,f,indent=1)

def verify_webhook(data, hmac_header ):
    digest = hmac.new(SECRET, data , hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))

def activate_response(request):
    data = request.get_data()
    verified = verify_token(data,request)
    print(verified)
    if not verified:
        abort(401)

    return clean_data(data)

@app.route('/eight/webhook/product_update', methods=['POST'])
def handle_webhook(file_to_submit=product_update_file):
    data = activate_response(request)
    data['id'] = int(data.get('id'))
    data['body_html'] = "".join(i if ord(i) < 128 else '' for i in re.sub(cleanr,'',data.get('body_html')))\
                                                                if data['body_html'] else data['body_html']
    submit_file(file_to_submit,data)
    return msg

@app.route('/eight/webhook/order_update',methods=['POST'])
def order_update(file_to_submit=order_update_file):
    data = activate_response(request)
    submit_file(file_to_submit,data)
    return msg
    
def inspect_file(file_name):
    if file_name not in os.listdir():
        assert ("file not in directory")
    
    with open(file_name,"r") as f: data = json.load(f)
    items_updated = iter(data.get("line_items"))
    while True:
        try:
            curr = next(items_updated)
            for k,v in curr.items():
                print(k)
        except StopIteration:
            break


    throw_away = 'shipping_lines'

if __name__ == "__main__":
    #app.run(debug=True)
    print()
    inspect_file(order_update_file)
 
      
