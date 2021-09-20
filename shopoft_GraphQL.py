from typing import List,Dict
from datetime import datetime
from .shopify_practise import FILE_PATH,change_status
import graphene as g
import asyncio
import requests as r

# DOING THE SIMILAT FUNCTIONALITY AS IN shopify practise only with graphQL

class graphQL_interactions(change_status):
    def __init__(self, file_path: str) -> None:
        super().__init__(file_path=FILE_PATH)
        self.endpoint = ""
        self.headers = {
            "content_type": "applications/json",
            "access_token": self.creds.get("password")
        }

    def sanitize_string(self,searchTerm:str) ->str:
        return " ".join(filter(str.isalpha(),searchTerm))

    async def fetch_products_by_id(self,id_no:str)->str:
        query = """ 
                query($id ID!){
                    product($id ID!) {
                        id
                        title
                    }
                }
                """
        variables = { id : id_no}
        submit_to_query = ""
        
        await asyncio.gather()


class Query(g.ObjectType):
    pass