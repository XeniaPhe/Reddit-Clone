from uuid import UUID
from core.models import Post, Content, User, Community
from core.custom_errors import post_not_found
from core.utils.service_utils import add_to_query_dict

def get_post(id: UUID):
    try:
        return Post.objects.get(pk=id)
    except Post.DoesNotExist:
        post_not_found(id)
        
def assert_post_exists(id: UUID):
    assert Post.objects.filter(content_id=id).exists(), f'Post with ID "{id}" does not exist'
    
def create_post(title: str, body: str, user: (str | User), community: (str | Community)):
    content = Content.objects.create(body=body, content_type=Content.ContentType.POST)
    
    query_dict = { 'title': title, }
    add_to_query_dict(query_dict, 'user', user)
    add_to_query_dict(query_dict, 'community', community)
    add_to_query_dict(query_dict, 'content', content)
    
    return Post.objects.create(**query_dict)