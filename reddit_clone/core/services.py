from uuid import UUID

from core.models import User, Community, Post, Comment
from core.custom_errors import user_not_found, community_not_found, post_not_found, comment_not_found

def get_user(username: str) -> User | None:
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        user_not_found(username)

def assert_user_exists(username: str):
    get_user(username)
    
def get_community(name: str) -> Community | None:
    try:
        return Community.objects.get(name=name)
    except Community.DoesNotExist:
        community_not_found(name)
        
def assert_community_exists(name: str):
    get_community(name)
    
def get_post(id: UUID):
    try:
        return Post.objects.get(id=id)
    except Post.DoesNotExist:
        post_not_found(id)
        
def assert_post_exists(id: UUID):
    get_post(id)
    
def get_comment(id: UUID):
    try:
        return Comment.objects.get(id=id)
    except Comment.DoesNotExist:
        comment_not_found(id)
        
def assert_comment_exists(id: UUID):
    get_comment(id)