from flask import Flask, request, abort
import hmac
import hashlib
import base64
import ssl
import shopify
from shopify_practise import change_status

app = Flask(__name__)

SECRET = bytes(change_status().creds.get("SECRET"),'utf-8')

def verify_webhook(data, hmac_header ):
    print(type(data))
    digest = hmac.new(SECRET, data , hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)

    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))


@app.route('/eight/webhook/product_update', methods=['POST'])
def handle_webhook():
    data = request.get_data()
    verified = verify_webhook(data, request.headers.get('X-Shopify-Hmac-SHA256'))

    if not verified:
        abort(401)

    # process webhook payload
    # ...
    pad = 16 - len(data) % 16
    data = data + (pad*chr(pad)).encode('utf-8')
    print ('Webhook verified', 200 )
    return data , 200

if __name__ == "__main__":
    app.run(debug=True)
