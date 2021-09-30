
from os import access
import re
from datetime import datetime
import psycopg2
from psycopg2.extras import Json,DictCursor
import pandas as pd
from collections import Counter
import hashlib
import random
from typing import Dict
from shopify_practise import change_status

access = change_status()

class connect_to_data():
    def __init__(self,table_name='order_bundles_d') -> None:
        self.con = None
        self.cursor = None
        self.table_name = table_name
        self.format_convertion = lambda s : "".join(re.split("[\[\' '\]\{\}]",s))
        self.format_str = lambda strs : self.format_convertion(str(strs)) if not(type(strs) == str) else strs
        self.__hash__ = lambda elem : int(hashlib.sha256(str(elem).encode('utf-8')).hexdigest(),16) % (10**random.randint(1,9))
    
    def __return_connection__(self):
        return psycopg2.connect(
            host=access.creds.get('host_pgs'),
            database=access.creds.get('database_pgs'),
            user=access.creds.get('user_pgs'),
            password=access.creds.get('password_postgres'),
            port=access.creds.get('port_pgs')
        )

    def __close__(self):
        self.con.close()

    def insert_into_table(self,meta_data:Dict)-> bool:
        self.con = self.__return_connction__()
        self.cursor = self.con.cursor(cursor_factory=DictCursor)
        instertion_json = self.staging_into_table(meta_data)
        c = self.view_columns()
        s_len = "%s" + "".join(", %s" for i in range(1,len(c)))
        query = f"""INSERT INTO {self.table_name} ({", ".join(c)}) values ({s_len}) ;"""
        hashed_order_id = self.__hash__(instertion_json.pop('order_id'))

        data = (Json(instertion_json),hashed_order_id)
        commited = False
        msg= "uploaded"
        try:
            self.cursor.execute(query,data)
            self.con.commit()
            commited = not(commited)


        except psycopg2.errors.UniqueViolation:
            msg =  f"{hashed_order_id} already registered in db" 
            self.con.rollback()
        
        finally:
            if self.con:
                
                self.__close__()
                            
            return commited,msg


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