import graphene
from functools import wraps
from core.custom_errors import graphql_error

SKIP_DEFAULT = 0
FIRST_DEFAULT = 10

class PaginatedList(graphene.List):
    def __init__(self, of_type, *args, **kwargs):
        kwargs.setdefault("skip", graphene.Argument(graphene.Int, required=False, default_value=SKIP_DEFAULT))
        kwargs.setdefault("first", graphene.Argument(graphene.Int, required=False, default_value=FIRST_DEFAULT))
        super().__init__(of_type, *args, **kwargs)

def paginate(func):
    @wraps(func)
    def wrapper(root, info, *args, **kwargs):
        skip = kwargs.get("skip", SKIP_DEFAULT)
        first = kwargs.get("first", FIRST_DEFAULT)
        
        queryset = func(root, info, *args, **kwargs)
        
        total_items = queryset.count()
        
        if skip >= total_items and skip != 0:
            graphql_error("Pagination Error:\nSkip value cannot be greater than or equal to total items.")
        
        total_pages = (total_items + first - 1) // first
        current_page = (skip // first) + 1
        page_size = first
        has_next_page = current_page < total_pages
        has_previous_page = current_page > 1
        paginated_queryset = queryset[skip : skip + first]
        
        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size,
            "has_next_page": has_next_page,
            "has_previous_page": has_previous_page,
            "items": paginated_queryset
        }