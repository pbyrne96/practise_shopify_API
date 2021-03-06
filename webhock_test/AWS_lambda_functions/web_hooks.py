
from typing import Dict
from flask import Flask,request, abort
import hmac
import hashlib
import base64
from shopify_practise import change_status
import json
import re
import os
from collections import Counter
from connect_to_df import connect_to_data
from datetime import datetime
# import shopify
# from flask_lambda import FlaskLambda




app = Flask(__name__)
data_insertion = connect_to_data()
    

        
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
target = 'sku'
grams_to_kilos = 0.001
datetime_format = "%Y-%m-%d %H:%M:%S"
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
    if not verified:
        abort(401)

    return clean_data(data)
    
def get_data_for_profitability_analysis(file_name=None):
    if not(file_name): file_name=order_update_file
    if file_name not in os.listdir(): assert ("file not in directory")
    
    with open(file_name,"r") as f: data = json.load(f)

    items_updated = iter(data.get("line_items"))
    is_discount,order_id,time_stamp = data.get("discount_codes"),data.get("id"),data.get("created_at")
    targets= ("sku","price","grams","total_discount","quantity")
    this_order_meta={}

    while True:
        try:
            curr = next(items_updated)
            t = {curr.get(targets[0]):{k:curr.get(k) for k in targets[1:]}}
            this_order_meta.update(t)
        except StopIteration:
            break
    
    this_order_meta["created_at"] = time_stamp
    t = this_order_meta["discount_codes"] = is_discount if is_discount else None

    return {order_id:this_order_meta}

def strip_to_datetime(dateString):
    return datetime.strptime(" ".join(re.split("[T+]",dateString)[:-1]),datetime_format).strftime(datetime_format)

def calc_net_prof_weight(dic):

    net_profit,weights = 0,0

    for k in list(dic.keys()):
        if target in k:
            params = dic.get(k)
            net_profit += params[0]
            weights += params[-1]
            dic.pop(k)
    dic["net_profit"] = net_profit
    dic["weight"] = net_profit
    return dic

def insert_bundle_data_for_insertion():

    most_recent_addition = get_data_for_profitability_analysis()
    order_profitability,sku_s = {},[]
    for key,value in most_recent_addition.get(*list(most_recent_addition.keys())).items():
        if key.isdigit():

            order_profitability[target+"_"+key] = [eval(f"""{value.get("price")} - {value.get("total_discount")} * {value.get("quantity")}"""),value.get("grams") * grams_to_kilos]
            sku_s.append(target+"_"+key)

        else:
            order_profitability[key] = value

    order_profitability["created_at"] = strip_to_datetime(order_profitability.get('created_at'))
    order_profitability["line_items"] = dict(Counter(sku_s))
    
    return {'order_id':{list(most_recent_addition.keys())[0]: calc_net_prof_weight(order_profitability)}}


def submit_order_to():
    data = insert_bundle_data_for_insertion()
    meta = data_insertion.insert_into_table(data)
    print(meta)
    submit_file(os.getcwd()+'/prac_staging.json',data)
    return meta

@app.route('/APP/eight/webhook/product_update', methods=['POST'])
def handle_webhook(file_to_submit=None):
    if not(file_to_submit): file_to_submit = product_update_file
    data = activate_response(request)
    data['id'] = int(data.get('id'))
    data['body_html'] = "".join(i if ord(i) < 128 else '' for i in re.sub(cleanr,'',data.get('body_html')))\
                                                                if data['body_html'] else data['body_html']

    return msg

@app.route('/APP/eight/webhook/order_update',methods=['POST'])
def order_update(file_to_submit=None):
    if not(file_to_submit): file_to_submit=order_update_file
    data = activate_response(request)
    submit_file(file_to_submit,data)
    submit_order_to()
    return msg

@app.route('/',methods=['GET'])
def home_welcome():
    return "<h1> WELCOME TO MY API </h1>"


def lambda_handler(event, context):

    request_type = event.get('httpMethod')
    
    if request_type in ['GET']:
        payload =  {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!')
        }
    elif request_type in ["POST"]:
        payload = {
            'statusCode': 500,
            'body': json.dumps("feck off")
        }
    return payload,context

if __name__ == "__main__":
    app.run(debug=True)
    print("*"*20)
    







      
