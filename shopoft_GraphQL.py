from typing import List,Dict
from datetime import datetime
from shopify_practise import FILE_PATH,change_status
import asyncio
import requests as r

# DOING THE SIMILAT FUNCTIONALITY AS IN shopify practise only with graphQL

class graphQL_interactions(change_status):
    def __init__(self, shop_name:str='weareeight',file_path:str=FILE_PATH ) -> None:
        super().__init__(file_path=FILE_PATH)
        self.endpoint = self.creds.get("graph_url").format(shop=shop_name)
        self.header = {'Content-Type': 'application/graphql',
                       'X-Shopify-Access-Token': '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'
                       }

    def sanitize_string(self,searchTerm:str) ->str:
        return " ".join(filter(str.isalpha(),searchTerm))

    def fetch_single_products_by_id(self,id_no:str)->str:
        query = """ 
            {
            product(id: "%s") {
                variants(first: 100) {
                edges {
                    node {
                    price
                    title
                    inventoryQuantity
                    }
                  }
                }
              }
            }
            """ %(str(id_no))
        
        return r.post(self.endpoint, 
                                data=query,
                                headers=self.header).json()


    def fetch_all_products(self,amount_to_view:str='10'):
        query = """
            { products(first: %s){
                
                edges{
                    node {
                        id
                        title
                        }
                    }    
                }
            }
            """ %(str(amount_to_view))
        
        return r.post(self.endpoint, data=query,headers=self.header).json()


if __name__ == "__main__":
    access = graphQL_interactions()
    print(access.fetch_all_products())
    print("**"*20)
    print(access.fetch_single_products_by_id("gid://shopify/Product/6966466937017"))