import graphene
from typing import Type
from functools import wraps
from django.db.models.query import QuerySet
from graphene_django.types import DjangoObjectType

from core.filters.filter_utils import get_graphene_filter_arguments, get_graphene_orderby_arguments, get_django_filter_arguments

def filtered_list(of_type: Type[DjangoObjectType], **kwargs):
    filter_arguments = get_graphene_filter_arguments(of_type)
    orderby_arguments = get_graphene_orderby_arguments(of_type)
    combined_kwargs = {**kwargs, **filter_arguments, **orderby_arguments}
    return graphene.List(of_type, **combined_kwargs)

def filter_queryset(graphene_model_type: Type[DjangoObjectType], queryset: QuerySet, **filter_params) -> QuerySet:
    filter_arguments = get_django_filter_arguments(graphene_model_type, **filter_params)
    queryset = queryset.filter(**filter_arguments)

def filter(graphene_model_type: Type[DjangoObjectType]):
    def decorator(func):
        wraps(func)
        def wrapper(root, info, *args, **kwargs):
            queryset = func(root, info, *args, **kwargs)
            return filter_queryset(graphene_model_type, queryset, **kwargs)
        return wrapper
    return decorator