from uuid import UUID
from core.models import Comment, Content, User, Post
from core.custom_errors import comment_not_found
from core.utils.service_utils import add_to_query_dict

def get_comment(id: UUID):
    try:
        return Comment.objects.get(pk=id)
    except Comment.DoesNotExist:
        comment_not_found(id)
        
def assert_comment_exists(id: UUID):
    assert Comment.objects.filter(id=id).exists(), f'Comment with id "{id}" does not exist'
    
def create_comment(body: str, parent: (UUID | Content), user: (str | User), post: (UUID | Post)):
    query_dict = {
        'body': body,
        'content_type': Content.ContentType.COMMENT,
    }
    
    add_to_query_dict(query_dict, 'user', user)
    
    content = Content.objects.create(**query_dict)
    
    query_dict.clear()
    add_to_query_dict(query_dict, 'parent', parent)
    add_to_query_dict(query_dict, 'post', post)
    add_to_query_dict(query_dict, 'content', content)
    
    return Comment.objects.create(**query_dict)