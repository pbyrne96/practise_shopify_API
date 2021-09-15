
import requests 
import re
from typing import List,Dict,Set,Callable
import os

FILE_PATH = os.path.join(os.getcwd(),"creditionals.txt")

class change_status:
    
    def __init__(self,file_path:str = None) -> None:
        
        self.file_path = FILE_PATH if not(file_path) else file_path
        self.search_creds = re.compile("=")
        self.search_draft = re.compile("draft")
        self.search_active = re.compile("active")
        self.replace_active = "active"
        self.replace_draft = "draft"
        self.creds = self.access_creds(self.file_path)

    def santitize_creditonals(self,file_path:str) -> Dict[str,str]:
        with open(file_path,"r") as f: creditionals = [i.replace("\n",'') for i in f.readlines()]
        index_split = lambda chr: self.search_creds.search(chr) 
        output={}
        for cred in creditionals:
            indexer = index_split(cred)
            ins = {cred[:indexer.span()[0]].strip() : cred[indexer.span()[0]+1:].strip()} if indexer else {}
            output.update(ins)
        yield output        

    def access_creds(self,file_path:str) -> Dict[str,str]:
        return next(iter(self.santitize_creditonals(file_path)))

    def check_endpoint(self,endpoint) -> str:
        check_dash = endpoint.find(r"/")
        return "/" + endpoint + "/" if not(check_dash>=0) else endpoint

    def return_endpoint(self,endpoint:str) -> Dict[str,str]:
        target_url = self.creds.get("url")+self.check_endpoint(endpoint).lower()
        return requests.get(target_url).json()

    def get_ids_by_status(self,ids_list:List[Dict[str,str]] , search_pattern: Callable = None)->list[str]:
        search_pattern = self.search_draft if not(search_pattern) else search_pattern
        target_keys=['id','status']
        return [i for i in  (", ".join(str(d.get(i)) for i in target_keys) for d in ids_list["products"]) if search_pattern.search(i)]

    def format_ids_for_staging_draft_active(self,ids_not_active:List[str]) -> None:
        return [i.replace(self.replace_draft,self.replace_active).split(",") for i in ids_not_active]

    def format_ids_for_staging_active_draft(self,ids_not_active:List[str]) -> None:
        return [i.replace(self.replace_active,self.replace_draft).split(",") for i in ids_not_active]
        
    def update_product_status(self,endpoint:str,prod_id:str,status:str) -> Dict[str,str]:
        payload = {"product":{"status": status}}
        destionation_url = self.creds.get("url") + self.check_endpoint(endpoint).lower() + str(prod_id) + ".json"
        r = requests.put(destionation_url,json=payload)
        try:
            return r.json()
        except Exception as e:
            return r

    def action_status(self,function_given:bool = False):
        endpoint = '/products/'
        function = self.format_ids_for_staging_draft_active if function_given else self.format_ids_for_staging_active_draft
        search_pattern = self.search_active if function else None
        print(function,search_pattern)
        format_for_staging = function(self.get_ids_by_status(self.return_endpoint('products.json')))
        return [self.update_product_status(endpoint,*list(map(str.strip,params))) for params in format_for_staging]

if __name__ == "__main__":
    access = change_status()
    access.action_status(False)
    
    # format_for_staging = self.format_ids_for_staging_draft_active(self.get_ids_by_status(self.return_endpoint('products.json')))
    # print(format_for_staging)
    # completed = [self.update_product_status(endpoint,*list(map(str.strip,params))) for params in format_for_staging]
    # return completed