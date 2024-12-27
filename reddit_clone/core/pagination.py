import graphene
from functools import wraps
from typing import Type
from django.db.models.query import QuerySet
from graphene_django.types import DjangoObjectType

from core.custom_errors import pagination_error, filter_error
from core.filters.filter import filter_queryset, get_all_graphene_kwargs_for_type

SKIP_DEFAULT = 0
FIRST_DEFAULT = 10

class _Metadata:
    def __init__(self, total_items: int, skip: int, first: int):
        self.total_items = total_items
        self.total_pages = (total_items + first - 1) // first
        self.total_pages = 1 if self.total_pages == 0 else self.total_pages
        self.page_size = first
        self.current_page = (skip // first) + 1
        self.has_next_page = self.current_page < self.total_pages
        self.has_previous_page = self.current_page > 1

class Metadata(graphene.ObjectType):
        total_items = graphene.Int()
        total_pages = graphene.Int()
        current_page = graphene.Int()
        page_size = graphene.Int()
        has_next_page = graphene.Boolean()
        has_previous_page = graphene.Boolean()
        
        def resolve_total_items(root, info): return root.total_items
        def resolve_total_pages(root, info): return root.total_pages
        def resolve_current_page(root, info): return root.current_page
        def resolve_page_size(root, info): return root.page_size
        def resolve_has_next_page(root, info): return root.has_next_page
        def resolve_has_previous_page(root, info): return root.has_previous_page
      
class _PaginatedList:
    def __init__(self, queryset: QuerySet, skip: int, first: int):
        self.items = queryset[skip: skip + first]
        self.page_info = _Metadata(queryset.count(), skip, first)
        
    @staticmethod
    def create(queryset: QuerySet, skip: int, first: int):
        if first <= 0:
            pagination_error('"first" must be greater than 0')
        elif skip < 0:
            pagination_error('"skip" must be greater than or equal to 0')
        elif skip >= queryset.count():
            pagination_error('"skip" cannot be greater than total item count')
            
        return _PaginatedList(queryset, skip, first)
        
def paginated_list(of_type: Type[DjangoObjectType], filter=False, **kwargs):
    class PaginatedList(graphene.ObjectType):
        page_info = graphene.Field(Metadata)
        items = graphene.List(of_type)
    
        def resolve_page_info(root, info): return root.page_info
        def resolve_items(root, info): return root.items
    
    kwargs = get_all_graphene_kwargs_for_type(of_type, **kwargs) if filter else kwargs
    
    return graphene.Field(PaginatedList,
                    skip=graphene.Argument(graphene.Int, required=False, default_value=SKIP_DEFAULT),
                    first=graphene.Argument(graphene.Int, required=False, default_value=FIRST_DEFAULT),
                    **kwargs)

def paginate(filter_for_type: Type[DjangoObjectType]=None):
    def decorator(func):
        @wraps(func)
        def wrapper(root, info, *args, **kwargs):
            queryset = func(root, info, *args, **kwargs)
            skip = kwargs.get("skip", SKIP_DEFAULT)
            first = kwargs.get("first", FIRST_DEFAULT)
            
            if filter_for_type is not None:
                if not hasattr(filter_for_type, '__bases__') or DjangoObjectType not in filter_for_type.__bases__:
                    filter_error('The "filter_for_type" argument must be a "DjangoObjectType" for filtering. '
                                f'Received: {filter_for_type.__name__ if hasattr(filter_for_type, '__name__') else filter_for_type}')
                
                queryset = filter_queryset(filter_for_type, queryset, **kwargs)
                
            return _PaginatedList(queryset, skip, first)
        return wrapper
    return decorator