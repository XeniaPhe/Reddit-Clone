from uuid import UUID
from django.db.models import F, Case, When, Value
from core.models import Comment, Content, User, Post, Membership
from core.services.content_service import assert_content
from core.custom_errors import comment_not_found, comment_deleted
from core.utils.service_utils import add_to_query_dict
from core.score_calculator import ActionType, OwnerType, ScoreType, get_score
from core.transact import transact
from core.utils.manager_utils import preselect
from core.auth.roles import GUEST, MEMBER, permission_granted

def get_comment(id: UUID, select_related: list[str]=None, prefetch_related: list[str]=None):
    try:
        return preselect(Comment, select_related, prefetch_related).get(pk=id)
    except Comment.DoesNotExist:
        comment_not_found(id)
        
def get_unremoved_comment(id: UUID, select_related: list[str]=None, prefetch_related: list[str]=None):
    if not select_related:
        select_related = ['content']
    elif 'content' not in select_related:
        select_related.append('content')
    
    comment = get_comment(id, select_related, prefetch_related)
    if comment.content.deleted:
        comment_deleted(id)
    
    return comment
        
def assert_comment_exists(id: UUID):
    get_comment(id)
    
def assert_comment(id: UUID):
    get_unremoved_comment(id)
    
def create_comment(body: str, parent: (UUID | Content), user: (str | User), post: (UUID | Post)):
    if not isinstance(parent, Content):
        assert_content(parent)
    
    query_dict = {
        'body': body,
        'content_type': Content.ContentType.COMMENT,
    }
    
    add_to_query_dict(query_dict, 'user', user)
    
    def transaction():
        content = Content.objects.create(**query_dict)

        query_dict.clear()
        add_to_query_dict(query_dict, 'parent', parent)
        add_to_query_dict(query_dict, 'post', post)
        add_to_query_dict(query_dict, 'content', content)

        username = user if isinstance(user, str) else user.username
        comment = Comment.objects.create(**query_dict)
        comment = get_comment(comment.id, select_related=['post', 'post__community', 'post__content',
                                                          'post__content__user', 'parent', 'parent__user'])
        _distribute_scores(comment, username)
        return (comment, content,)
    
    return transact(transaction, 'An error occured while creating the comment')

def _distribute_scores(comment: Comment, username: str):
    parent_is_comment = comment.parent.is_comment()
    action_type = ActionType.COMMENT_UNDER_COMMENT if parent_is_comment else ActionType.COMMENT_UNDER_POST
    
    updates = {
        'karma': {},
        'engagement': {},
    }
    
    karma_gained = get_score(action_type, OwnerType.ACTOR, ScoreType.KARMA)
    activity_gained = get_score(action_type, OwnerType.ACTOR, ScoreType.ACTIVITY_SCORE)
    updates['karma'][username] = karma_gained
    
    query_dict = {}
    add_to_query_dict(query_dict, 'user', username)
    add_to_query_dict(query_dict, 'community', comment.post.community.name)
    
    membership = Membership.objects.filter(**query_dict).first()
    if membership is None:
        query_dict['role'] = GUEST
        query_dict['activity_score'] = activity_gained
        Membership.objects.create(**query_dict)
    else:
        if permission_granted(MEMBER, membership.role):
            activity_gained *= 2
            
        Membership.objects.filter(**query_dict).update(activity_score = F('activity_score') + activity_gained)
    
    karma_gained = get_score(action_type, OwnerType.POST_OWNER, ScoreType.KARMA)
    engagement_gained = get_score(action_type, OwnerType.POST_OWNER, ScoreType.ENGAGEMENT_SCORE)
    updates['karma'][comment.post.content.user.username] = karma_gained
    updates['engagement'][comment.post.content.id] = engagement_gained
    
    if parent_is_comment:
        karma_gained = get_score(action_type, OwnerType.COMMENT_OWNER, ScoreType.KARMA)
        engagement_gained = get_score(action_type, OwnerType.COMMENT_OWNER, ScoreType.ENGAGEMENT_SCORE)
        updates['karma'][comment.parent.user.username] = karma_gained
        updates['engagement'][comment.parent.id] = engagement_gained
        
    update_karma_expr = Case(
        *[When(username=usr, then = F('karma') + Value(delta))
          for usr, delta in updates['karma'].items()],
        default=F('karma'))
    
    update_engagement_expr = Case(
        *[When(id=uid, then = F('engagement_score') + Value(delta))
          for uid, delta in updates['engagement'].items()],
        default=F('engagement_score'))
    
    User.objects.filter(username__in=updates['karma'].keys()).update(karma=update_karma_expr)
    Content.objects.filter(id__in=updates['engagement'].keys()).update(engagement_score=update_engagement_expr)