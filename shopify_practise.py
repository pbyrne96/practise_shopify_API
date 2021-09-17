
import requests 
import re
from typing import List,Dict,Callable
from collections import ChainMap
import os
from datetime import datetime

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
        self.order = [self.replace_draft,self.replace_active]
        self.endpoint = '/products/'
        self.inital_target = "products.json"
        self.created_at_format = "%Y-%m-%d %H:%M:%S"
        self.today_diff = lambda strs_date :\
            datetime.strptime(str(datetime.today().strftime(self.created_at_format)),self.created_at_format).day - strs_date.day
        

    def santitize_creditonals(self,file_path:str) -> Dict[str,str]:
        with open(file_path,"r") as f: creditionals = [i.replace("\n",'') for i in f.readlines()]
        index_split = lambda chr: self.search_creds.search(chr) 
        for cred in creditionals:
            indexer = index_split(cred)
            yield {cred[:indexer.span()[0]].strip() : cred[indexer.span()[0]+1:].strip()} if indexer else {}
      
    def access_creds(self,file_path:str) -> Dict[str,str]:
        return dict(ChainMap(*list(self.santitize_creditonals(file_path))))

    def check_endpoint(self,endpoint) -> str:
        check_dash = endpoint.find(r"/")
        return "/" + endpoint + "/" if not(check_dash>=0) else endpoint

    def return_endpoint(self,endpoint:str) -> Dict[str,str]:
        target_url = self.creds.get("url")+self.check_endpoint(endpoint).lower()
        return requests.get(target_url).json()

    def check_low_inventory_status(self,lim:int=10):
        products_data = self.return_endpoint(self.inital_target)
        l = products_data[self.inital_target.split(".")[0]]
        output = {}
        [output.update(l[idx]) for idx in range(len(l)) if (l[idx].get("variants")[0].get("inventory_quantity")) < lim]
        return self.change_status(self.get_ids_by_status({"products":[output]},self.search_active)) if output else output

    def caclulate_ROS(self,units_sold , oriingal_amount) -> float:
        try:
            return (units_sold/oriingal_amount)  * 100
        except ZeroDivisionError:
            return 0.0

    def apply_lower_price(self,price:float,discount:float=.10) -> float:
        return float(price) - float(price) * discount

    def get_low_rate_of_sale(self,
                            lim_days=1,
                            lim_ros=80.0)\
                            -> List[Dict[str,str]]:
                            
        products_data = self.return_endpoint(self.inital_target)
        for_discount=[]
        for idx in range(len(products_data.get("products"))):
            
            curr = products_data.get("products")[idx].get("variants")[0]
            strs = curr.get("created_at")
            period_selling = self.today_diff(datetime.strptime(strs.replace(strs[strs.find("".join(i for i in strs if i.isalpha()))]," ").split("+")[0] , self.created_at_format))
            ros = self.caclulate_ROS(curr.get("inventory_quantity"),curr.get("old_inventory_quantity"))

            if (period_selling >= lim_days ) and (ros >= lim_ros):
                for_discount.append(products_data.get("products")[idx])

        return for_discount
    
    def insert_price_change(self)->None:
        for_discount = self.get_low_rate_of_sale()
        for d in for_discount:
            update = d.get("variants")[0]
            update["price"] = self.apply_lower_price(update.get("price"))
            yield update
        
    def access_price_change_staging(self):
        return list(self.insert_price_change())
    
    def apply_price_changes(self):
        return [self.update_prices(self.endpoint,str(d.get("product_id")),{"product":{"variant":d }})\
            for d in self.access_price_change_staging() ]

    def get_ids_by_status(self,
                          ids_list:List[Dict[str,str]],
                          search_pattern: re.Pattern = None)\
                          ->list[str]:

        search_pattern = self.search_draft if not(search_pattern) else search_pattern
        target_keys=['id','status']
        return [i for i in  (", ".join(str(d.get(i)) for i in target_keys) for d in ids_list["products"]) if search_pattern.search(i)]

    def format_ids_for_staging(self,
                              ids_not_active:List[str],
                              draft_replace:bool=True)-> List[str]:
        if not(draft_replace): self.order=self.order[::-1]
        return [i.replace(self.order[0],self.order[-1]).split(",") for i in ids_not_active]
        
    def update_product_status(self,
                             endpoint:str,
                             prod_id:str,
                             status:str)\
                             -> Dict[str,str]:
        
        payload = {"product":{"status": status}} 
        destionation_url = self.creds.get("url") + self.check_endpoint(endpoint).lower() + str(prod_id) + ".json"
        return self.submit_put_request(destionation_url,payload)

    def update_prices(self,
                    endpoint:str,
                    prod_id:str,
                    payload:Dict[str,str])\
                    -> Dict[str,str]:

        destination_url = self.creds.get("url") + endpoint.lower() + str(prod_id) + ".json"
        return self.submit_put_request(destination_url , payload)

    def submit_put_request(self,destionation_url:str,payload:Dict[str,str]):
        r = requests.put(destionation_url,json=payload)
        try:
            return r.json()
        except Exception as e:
            return r

    def change_status(self,staging_list:List[str]) ->List[Dict[str,str]]:
        format_for_staging = self.format_ids_for_staging(staging_list,False)
        return [access.update_product_status(self.endpoint,*list(map(str.strip,params))) for params in format_for_staging]

if __name__ == "__main__":

    access = change_status()
    print(access.apply_price_changes())

 
