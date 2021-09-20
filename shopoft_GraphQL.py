from typing import List,Dict
from datetime import datetime
from .shopify_practise import FILE_PATH,change_status
import graphene as g


# DOING THE SIMILAT FUNCTIONALITY AS IN shopify practise only with graphQL

class graphQL_interactions(change_status):
    def __init__(self, file_path: str) -> None:
        super().__init__(file_path=FILE_PATH)
    
    def sanitize_search_term(self,searchTerm:str) ->str:
        return " ".join(filter(str.isalpha(),searchTerm))

    def fetch_products_by_termß(self,search_term)->str:
        query = search_term


class Query(g.ObjectType):
    pass