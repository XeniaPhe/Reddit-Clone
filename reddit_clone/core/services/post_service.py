from uuid import UUID
from django.db.models import Sum
from core.models import Post, Content, User, Community
from core.custom_errors import post_not_found

def get_post(id: UUID):
    try:
        return Post.objects.get(id=id)
    except Post.DoesNotExist:
        post_not_found(id)
        
def assert_post_exists(id: UUID):
    get_post(id)
    
def create_post(title: str, body: str, user: User, community: Community):
    content = Content.objects.create(body=body, content_type=Content.ContentType.POST)
    return Post.objects.create(title=title, user=user, community=community, content=content)

def get_posts_with_total_votes(**filters):
    return Post.objects.filter(**filters).annotate(total_votes=Sum('content__votes__vote'))