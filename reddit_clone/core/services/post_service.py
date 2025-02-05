from uuid import UUID
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, IntegerField
from django.db.models.functions import ExtractHour
from core.models import Post, Content, User, Community, Membership
from core.custom_errors import post_not_found, post_deleted
from core.utils.service_utils import add_to_query_dict
from core.score_calculator import ActionType, OwnerType, ScoreType, get_score
from core.transact import transact
from core.utils.manager_utils import preselect
from core.services.community_service import assert_community_exists

def get_post(id: UUID, select_related: list[str]=None, prefetch_related: list[str]=None):
    try:
        return preselect(Post, select_related, prefetch_related).get(pk=id)
    except Post.DoesNotExist:
        post_not_found(id)

def get_unremoved_post(id: UUID, select_related: list[str]=None, prefetch_related: list[str]=None):
    if not select_related:
        select_related = ['content']
    elif 'content' not in select_related:
        select_related.append('content')
    
    post = get_post(id, select_related, prefetch_related)
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
    
    def transaction():
        content = Content.objects.create(**query_dict)
    
        query_dict = { 'title': title, }
        add_to_query_dict(query_dict, 'community', community)
        add_to_query_dict(query_dict, 'content', content)
    
        post = Post.objects.create(**query_dict)
        
        karma_gained = get_score(ActionType.WRITE_POST, OwnerType.ACTOR, ScoreType.KARMA)
        activity_gained = get_score(ActionType.WRITE_POST, OwnerType.ACTOR, ScoreType.ACTIVITY_SCORE) * 2
        username = user if isinstance(user, str) else user.username
        
        User.objects.filter(username=username).update(karma = F('karma') + karma_gained)
        
        query_dict.pop('content')
        query_dict.pop('title')
        query_dict.pop('content_type')
        query_dict.pop('body')
        
        Membership.objects.filter(**query_dict).update(activity_score = F('activity_score') + activity_gained)
        return (post, content,)
    
    return transact(transaction, 'An error occured while creating the post')

def hot_posts(community_name: str=None):
    if community_name:
        assert_community_exists(community_name)
        posts = Post.objects.filter(community_id=community_name)
    else:
        posts = Post.objects.all()
    
    return (posts
            .select_related('content')
            .annotate(
                hours_since_publish = ExpressionWrapper(
                    ExtractHour(timezone.now() - F('content__publish_date')),
                    output_field=IntegerField()
                )
            )
            .annotate(
                engagement_per_hour = ExpressionWrapper(
                    F('engagement_score') / F('hours_since_publish'),
                    output_field=IntegerField()
                )
            )
            .order_by('-engagement_per_hour'))