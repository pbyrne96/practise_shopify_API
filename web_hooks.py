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

access = change_status().creds
SECRET = bytes(access.get("SECRET"),'utf-8')
shop_url = access.get("url")
end_file = os.getcwd()+"/staging.json"
cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

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
    data['id'] = int(data.get('id'))
    data['body_html'] = "".join(i if ord(i) < 128 else '' for i in re.sub(cleanr,'',data.get('body_html')))
    with open(end_file,"w") as f: json.dump(data,f,indent=1)
    return "Webhook received.",200


if __name__ == "__main__":
    app.run(debug=True)
