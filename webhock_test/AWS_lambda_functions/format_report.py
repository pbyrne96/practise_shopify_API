from ast import Str
import collections
from shopify_practise import change_status
from connect_to_df import connect_to_data
import pandas as pd
from functools import reduce
from datetime import datetime
import re
import json
from typing import Dict, Iterator,List,Iterable

access = change_status()

db_connection = connect_to_data().__return_connection__()

table_name = "order_bundles_d"
date_form = "%Y-%m-%d %H"
split_data = lambda date_str : datetime.strftime(datetime.strptime(" ".join(date_str.split(':')[:1]),date_form),date_form)
clean_type_command = lambda strs : strs.find(r"'")
float_type = float
line_items = 'line_items'

def fetch_data(table=table_name)->Dict[str,str]:
    query = f""" SELECT * FROM {table} """
    dataframe = pd.read_sql_query(query,db_connection)
    return {keys:data for keys,data in list(zip(dataframe['order_id'].values,dataframe['dict'].values))}
    
def group_by_date()->Iterable:
    for k,v in fetch_data().items():
        key = v.pop('created_at')
        v['_id'] = k
        yield {key:v}

def access_group(dic=None)->Dict[str,str]:
    if not(dic): dic = list(group_by_date())
    return reduce(lambda a,b: dict(**a,**b),dic)

def group_by_dd_mm(dic)->Dict[str,str]:
    output = {k:{k:[] for k in list(dic.get(list(dic.keys())[0]))} for k in list(set(split_data(i) for i in list(dic.keys())))}
    for k,v in dic.items():
        date_str = split_data(k)
        access = output.get(date_str)
        {key:access.get(key).append(v.get(key)) for key in access.keys()}
    return output

def check_len(lis,target='None')->bool:
    return lis.count(target)==len(lis)

def to_dict(lis)->List[str]:
    return [i for i in lis if i[0].isalpha()]

def format_line_items(line_items)->Dict[str,str]:

    dd = collections.defaultdict(list)
    for v in [dict(collections.Counter(to_dict(re.split(r"[: ' ',]",i)))) for i in line_items]:
        for k,val in v.items():
            dd[k].append(val)
    
    return {k:sum(list(map(int,dd.get(k)))) for k in dd.keys()}
    
def cleae_None(l)-> str:
    return ' '.join(list(filter(None,l))) if not(check_len(l)) else []

def calc_sum_l(l) -> float:

    if float_type not in list(set(map(type,l))):

        try:

            return sum(list(map(float,l)))
        except Exception as e:

            raise('incompatable data types')

    return sum(l)

def format_layers(vals)->Dict[str]:
    return {
        'discount_codes': cleae_None(vals.get('discount_codes')),
        'line_items': format_line_items(vals.get('line_items')),
        'net_profit': calc_sum_l(vals.get('net_profit')),
        'weight': calc_sum_l(vals.get('weight')),
    }

def deep_get(d,keys,default=None)->Dict[str,str]:
    assert type(keys) is list
    if d is None:
        return default
    if not keys:
        return d
    return deep_get(d.get(keys[0]), keys[1:])

def dictoinary_to_pd(dic):
    return pd.DataFrame.from_dict(dic,orient='index')

def get_report_by_hh()->tuple(Dict[str,str],pd.DataFrame):

    def _innr_get():
        for k,layer in group_by_dd_mm(access_group()).items():
            yield {k:format_layers(layer)}

    dict_for_analysis = access_group(list(_innr_get()))
    main_data = dictoinary_to_pd(dict_for_analysis)
    line_items_dict={k:deep_get(dict_for_analysis,[k,line_items]) for k in dict_for_analysis}
    return line_items_dict,main_data



print(get_report_by_hh())