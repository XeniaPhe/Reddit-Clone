import graphene
from typing import Type
from graphene_django.types import DjangoObjectType

from core.filters.filter import filtered_list
from core.pagination import paginated_list, paginate

def get_list(of_type: Type[DjangoObjectType], filter=False, paginate=False, **kwargs):
    if filter == False and paginate == False:
        return graphene.List(of_type, **kwargs)
    elif filter == True and paginate == False:
        return filtered_list(of_type, **kwargs)
    
    return paginated_list(of_type, filter, **kwargs)
    
def filter_and_paginate(graphene_model_type: Type[DjangoObjectType]):
    return paginate(graphene_model_type)