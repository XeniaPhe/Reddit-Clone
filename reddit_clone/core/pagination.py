import graphene
from functools import wraps
from typing import Type
from django.db.models.query import QuerySet

from core.custom_errors import graphql_error

SKIP_DEFAULT = 0
FIRST_DEFAULT = 10

class _Metadata:
    def __init__(self, total_items: int, skip: int, first: int):
        self.total_items = total_items
        self.total_pages = (total_items + first - 1) // first
        self.page_size = first
        self.current_page = (skip // first) + 1
        self.has_next_page = self.current_page < self.total_pages
        self.has_previous_page = self.current_page > 1

class _PaginatedList:
    def __init__(self, queryset: QuerySet, skip: int, first: int):
        self.items = queryset[skip: skip + first]
        self.metadata = _Metadata(queryset.count(), skip, first)
        
    @staticmethod
    def create(queryset: QuerySet, skip: int, first: int):
        if first <= 0:
            graphql_error('Pagination Error:\"first" must be greater than 0')
        elif skip < 0:
            graphql_error('Pagination Error: "skip" must be greater than or equal to 0')
        elif skip >= queryset.count():
            graphql_error("Pagination Error:\nskip cannot be greater than total item count")
            
        return _PaginatedList(queryset, skip, first)
        
def paginated_list(of_type: Type, **kwargs):
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
    
    class PaginatedList(graphene.ObjectType):
        items = graphene.List(graphene.NonNull(of_type))
        metadata = graphene.Field(Metadata)
    
        def resolve_items(root, info): return root.items
        def resolve_metadata(root, info): return root.metadata
        
    return graphene.Field(PaginatedList,
                   skip=graphene.Argument(graphene.Int, required=False, default_value=0),
                   first=graphene.Argument(graphene.Int, required=False, default_value=10),
                   **kwargs)

def paginate(func):
    @wraps(func)
    def wrapper(root, info, *args, **kwargs):
        queryset = func(root, info, *args, **kwargs)
        skip = kwargs.get("skip", SKIP_DEFAULT)
        first = kwargs.get("first", FIRST_DEFAULT)
        return _PaginatedList.create(queryset, skip, first)
    return wrapper