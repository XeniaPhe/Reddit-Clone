from uuid import UUID
from django.db.models import Sum
from core.models import Comment, Content, User, Post
from core.custom_errors import comment_not_found

def get_comment(id: UUID):
    try:
        return Comment.objects.get(id=id)
    except Comment.DoesNotExist:
        comment_not_found(id)
        
def assert_comment_exists(id: UUID):
    get_comment(id)
    
def create_comment(body: str, parent: Content, user: User, post: Post):
    content = Content.objects.create(body=body, content_type=Content.ContentType.COMMENT)
    return Comment.objects.create(parent=parent, user=user, post=post, content=content)

def get_comments_with_total_votes(**filters):
    return Comment.objects.filter(**filters).annotate(total_votes=Sum('content__votes__vote'))

def get_comment_with_total_votes(id: UUID):
    return get_comments_with_total_votes(id=id).first()