from typing import Dict
from flask import Flask,request, abort
import hmac
import hashlib
import base64
from shopify_practise import change_status
import os
import json
import re
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import Json,DictCursor
import pandas as pd
from collections import Counter
# import shopify
# from flask_lambda import FlaskLambda


class connect_to_data():
    def __init__(self,table_name='order_bundles_d') -> None:
        self.con = psycopg2.connect(
            host='localhost',
            database='optim',
            user='postgres',
            password='BallsBridge46',
            port=5432
        )
        self.cursor = self.con.cursor(cursor_factory=DictCursor)
        self.table_name = table_name
        self.format_convertion = lambda s : "".join(re.split("[\[\' '\]\{\}]",s))
        self.format_str = lambda strs : self.format_convertion(str(strs)) if not(type(strs) == str) else strs

    def __close__(self):
        self.con.close()

    def insert_into_table(self,meta_data:Dict)-> bool:
        instertion_json = self.staging_into_table(meta_data)
        c = self.view_columns()
        s_len = "%s" + "".join(", %s" for i in range(1,len(c)))
        query = f"""INSERT INTO {self.table_name} ({", ".join(c)}) values ({s_len}) ;"""
        order_id = instertion_json.pop('order_id')
        data = (Json(instertion_json),order_id)
        commited = False

        try:
            self.cursor.execute(query,data)
            self.con.commit()
            commited = not(commited)

        except psycopg2.errors.UniqueViolation:
            print( f"{order_id} already registered in db" )

        finally:
            return commited


    def view_columns(self):
        query = f""" SELECT * FROM {self.table_name} """
        return sorted(pd.read_sql_query(query,self.con).columns)

    def staging_into_table(self,meta:Dict) -> None:
        def _merge(meta):
            return {k:v for k,v in meta[0].items()}

        outstanding = {}
        for k in meta:
            
            if isinstance(meta.get(k),dict):
                outstanding.update({**{k:list(meta.get(k).keys())[0]},**_merge(list(meta.get(k).values()))})
            else:
                outstanding[k] = meta.get(k)

        return {k:self.format_str(outstanding.get(k)) for k in outstanding}


class flask_api:
    app = Flask(__name__)
    def __init__(self) -> None:
        
        self.access = change_status().creds
        self.SECRET = bytes(self.access.get("SECRET"),'utf-8')
        HMAC_STR = 'X-Shopify-Hmac-SHA256'

        self.shop_url = self.access.get("url")
        self.product_update_file = os.getcwd()+"/staging.json"
        self.order_update_file = os.getcwd()+"/order_update.json"
        self.customer_records_file = os.getcwd() + "/customer_records.json"

        self.cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        self.verify_token = lambda data, r: self.verify_webhook(data,r.headers.get(HMAC_STR))
        self.clean_data = lambda data : json.loads(data.decode('utf-8'))
        self.target = 'sku'
        self.grams_to_kilos = 0.001
        self.datetime_format = "%Y-%m-%d %H:%M:%S"
        self.msg = "Webhook received.",200

    def submit_file(self,file_to_submit,data):
        with open(file_to_submit,"w") as f: json.dump(data,f,indent=1)

    def verify_webhook(self,data, hmac_header ):
        digest = hmac.new(self.SECRET, data , hashlib.sha256).digest()
        computed_hmac = base64.b64encode(digest)
        return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))

    def activate_response(self,request):
        data = request.get_data()
        verified = self.verify_token(data,request)
        if not verified:
            abort(401)

        return self.clean_data(data)

    @app.route('/APP/eight/webhook/product_update', methods=['POST'])
    def handle_webhook(self,file_to_submit=None):
        if not(file_to_submit): file_to_submit = self.product_update_file
        data = self.activate_response(request)
        data['id'] = int(data.get('id'))
        data['body_html'] = "".join(i if ord(i) < 128 else '' for i in re.sub(self.cleanr,'',data.get('body_html')))\
                                                                    if data['body_html'] else data['body_html']
        self.submit_file(file_to_submit,data)
        return self.msg

    @app.route('/APP/eight/webhook/order_update',methods=['POST'])
    def order_update(self,file_to_submit=None):
        if not(file_to_submit): file_to_submit=self.order_update_file
        data = self.activate_response(request)
        self.submit_file(file_to_submit,data)
        return (200,data)
        
    def get_data_for_profitability_analysis(self,file_name=None):
        if not(file_name): file_name=self.order_update_file
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

    def strip_to_datetime(self,dateString):
        return datetime.strptime(" ".join(re.split("[T+]",dateString)[:-1]),self.datetime_format).strftime(self.datetime_format)

    def calc_net_prof_weight(self,dic):

        net_profit,weights = 0,0

        for k in list(dic.keys()):
            if self.target in k:
                params = dic.get(k)
                net_profit += params[0]
                weights += params[-1]
                dic.pop(k)
        dic["net_profit"] = net_profit
        dic["weight"] = net_profit
        return dic

    def insert_bundle_data_for_insertion(self):

        most_recent_addition = self.get_data_for_profitability_analysis()
        order_profitability,sku_s = {},[]
        for key,value in most_recent_addition.get(*list(most_recent_addition.keys())).items():
            if key.isdigit():

                order_profitability[self.target+"_"+key] = [eval(f"""{value.get("price")} - {value.get("total_discount")} * {value.get("quantity")}"""),value.get("grams") * self.grams_to_kilos]
                sku_s.append(self.target+"_"+key)

            else:
                order_profitability[key] = value

        order_profitability["created_at"] = self.strip_to_datetime(order_profitability.get('created_at'))
        order_profitability["line_items"] = dict(Counter(sku_s))
        return {'order_id':{list(most_recent_addition.keys())[0] : self.calc_net_prof_weight(order_profitability)}}


def lambda_handler(event, context):
    # TODO implement

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
    return payload

if __name__ == "__main__":
    #app.run(debug=True)
    flask_app = flask_api()
    # flask_app.app.run(debug=True)
    print("*"*20)
    meta = flask_app.insert_bundle_data_for_insertion()
    connect = connect_to_data()
    print(connect.insert_into_table(meta))





      
