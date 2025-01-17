from uuid import UUID
from django.db.models import F
from core.models import Comment, Content, User, Post
from core.services.content_service import assert_content, get_related_object
from core.custom_errors import comment_not_found, comment_deleted
from core.utils.service_utils import add_to_query_dict
from core.score_calculator import ActionType, ContentType, ScoreType, get_score
from core.transact import transact
from core.utils.manager_utils import preselect

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

        comment = Comment.objects.create(**query_dict)
        comment = get_comment(comment.id, select_related=['parent', 'parent__user', 'post', 'post__content', 'post__content__user'])
        username = user if isinstance(user, str) else user.username
        _distribute_scores(comment, username)
        return (comment, content,)
    
    return transact(transaction, 'An error occured while creating the comment')

def _distribute_scores(comment: Comment, username: str):
    karma_gained = get_score(ActionType.WRITE_COMMENT, ContentType.COMMENT, ScoreType.KARMA)
    User.objects.filter(username=username).update(karma = F('karma') + karma_gained)
    
    if comment.parent.is_post():
        engagement_gained = get_score(ActionType.COMMENT_UNDER_POST, ContentType.POST, ScoreType.ENGAGEMENT_SCORE)
        karma_gained = get_score(ActionType.COMMENT_UNDER_POST, ContentType.POST, ScoreType.KARMA)
        Content.objects.filter(id=comment.parent.id).update(engagement_score = F('engagement_score') + engagement_gained)
        User.objects.filter(username=comment.parent.user.username).update(karma = F('karma') + karma_gained)
    else:
        engagement_gained = get_score(ActionType.COMMENT_UNDER_COMMENT, ContentType.POST, ScoreType.ENGAGEMENT_SCORE)
        karma_gained = get_score(ActionType.COMMENT_UNDER_COMMENT, ContentType.POST, ScoreType.KARMA)
    
        Content.objects.filter(id=comment.post.content.id).update(engagement_score = F('engagement_score') + engagement_gained)
        User.objects.filter(username=comment.post.content.user.username).update(karma = F('karma') + karma_gained)
        
        content = comment.parent
        for i in range(0, 4):
            engagement_gained = get_score(ActionType.COMMENT_UNDER_COMMENT, ContentType.COMMENT, ScoreType.ENGAGEMENT_SCORE, order_index=i)
            karma_gained = get_score(ActionType.COMMENT_UNDER_COMMENT, ContentType.COMMENT, ScoreType.KARMA, order_index=i)
            
            Content.objects.filter(id=content.id).update(engagement_score = F('engagement_score') + engagement_gained)
            User.objects.filter(username=content.user.username).update(karma = F('karma') + karma_gained)
            
            content = get_related_object(content, select_related=['parent', 'parent__user']).parent
            if content.is_post():
                break