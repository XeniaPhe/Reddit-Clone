from core.models import Community
from core.custom_errors import community_not_found

def get_community(name: str) -> Community | None:
    try:
        return Community.objects.get(name=name)
    except Community.DoesNotExist:
        community_not_found(name)
        
def assert_community_exists(name: str):
    get_community(name)