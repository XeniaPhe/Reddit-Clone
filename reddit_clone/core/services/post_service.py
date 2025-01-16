from uuid import UUID
from django.db.models import F
from core.models import Post, Content, User, Community
from core.custom_errors import post_not_found, post_deleted
from core.utils.service_utils import add_to_query_dict
from core.services.score_service import ActionType, ContentType, ScoreType, get_score

def get_post(id: UUID):
    try:
        return Post.objects.get(pk=id)
    except Post.DoesNotExist:
        post_not_found(id)

def get_unremoved_post(id: UUID):
    post = get_post(id)
    if post.content.deleted:
        post_deleted(id)
        
    return post
        
def assert_post_exists(id: UUID):
    get_post(id)

def assert_post(id: UUID):
    get_unremoved_post(id)
    
def create_post(title: str, body: str, user: (str | User), community: (str | Community)):
    query_dict = {
        'body': body,
        'content_type': Content.ContentType.POST,
    }
    
    add_to_query_dict(query_dict, 'user', user)
    content = Content.objects.create(**query_dict)
    
    query_dict = { 'title': title, }
    add_to_query_dict(query_dict, 'community', community)
    add_to_query_dict(query_dict, 'content', content)
    
    post = Post.objects.create(**query_dict)
    karma_gained = get_score(ActionType.WRITE_POST, ContentType.POST, ScoreType.KARMA)
    username = user if isinstance(user, str) else user.username
    User.objects.filter(username=username).update(karma = F('karma') + karma_gained)
    
    return post