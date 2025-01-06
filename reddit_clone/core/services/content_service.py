from uuid import UUID
from core.models import Content
from core.custom_errors import content_not_found

def get_content(id: UUID):
    try:
        return Content.objects.get(id=id)
    except Content.DoesNotExist:
        content_not_found(id)
        
def assert_content_exists(id: UUID):
    get_content(id)