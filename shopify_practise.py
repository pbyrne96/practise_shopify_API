
import requests 
import re
from typing import List,Dict,Set,Callable
import os

FILE_PATH = os.path.join(os.getcwd(),"creditionals.txt")

search_creds = re.compile("=")

def santitize_creditonals(file_path) -> Dict[str,str]:
    with open(file_path,"r") as f: creditionals = [i.replace("\n",'') for i in f.readlines()]
    index_split = lambda chr: search_creds.search(chr) 
    output={}
    for cred in creditionals:
        indexer = index_split(cred)
        ins = {cred[:indexer.span()[0]].strip() : cred[indexer.span()[0]+1:].strip()} if indexer else {}
        output.update(ins)
    yield output        

def access_creds(file_path=FILE_PATH) -> Dict[str,str]:
    return next(iter(santitize_creditonals(file_path)))

def check_endpoint(endpoint) -> str:
    check_dash = endpoint.find(r"/")
    return "/" + endpoint + "/" if not(check_dash>=0) else endpoint

def return_endpoint(endpoint) -> Dict[str,str]:
    creds = access_creds()
    target_url = creds.get("url")+check_endpoint(endpoint).lower()
    return requests.get(target_url).json()
    
def update_product_status(endpoint,prod_id,status) -> int:
    creds = access_creds()
    payload = {"product":{"status": status}}
    destionation_url = creds.get("url") + check_endpoint(endpoint).lower() + str(prod_id) + ".json"
    return requests.put(destionation_url,json=payload).json()



if __name__ == "__main__":
    creds = access_creds()
    print(creds)