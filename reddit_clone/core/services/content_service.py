from uuid import UUID
from django.db.models import F
from core.models import Content, User, Comment, Post, Vote, Community, Membership
from core.custom_errors import content_not_found, content_deleted
from core.score_calculator import VoteType, ActionType, ScoreType, OwnerType, get_score
from core.utils.service_utils import add_to_query_dict
from core.transact import transact
from core.utils.manager_utils import preselect
from core.auth.roles import GUEST, MEMBER, permission_granted

def get_content(id: UUID, select_related: list[str]=None, prefetch_related: list[str]=None):
    try:
        return preselect(Content, select_related, prefetch_related).get(id=id)
    except Content.DoesNotExist:
        content_not_found(id)
        
def get_unremoved_content(id: UUID, select_related: list[str]=None, prefetch_related: list[str]=None):
    content = get_content(id, select_related, prefetch_related)
    if content.deleted:
        content_deleted(id)
        
    return content
        
def assert_content_exists(id: UUID):
    get_content(id)
    
def assert_content(id: UUID):
    get_unremoved_content(id)

def get_related_object(content: Content, select_related: list[str]=None, prefetch_related: list[str]=None):
    preselect(Comment if content.is_comment() else Post, select_related, prefetch_related).get(id=content.id)

def get_user_vote(content: (UUID | Content), user: (str | User)):
    if not isinstance(content, Content):
        assert_content(content)
        
    query_dict = {}
    add_to_query_dict(query_dict, 'content', content)
    add_to_query_dict(query_dict, 'user', user)
    
    vote = Vote.objects.filter(**query_dict).only('vote').first()
    return None if not vote else vote.vote

def vote_content(content: (UUID | Content), voter: (str | User), vote: int) -> int:
    query_dict = {}
    add_to_query_dict(query_dict, 'content', content)
    add_to_query_dict(query_dict, 'user', voter)
    
    user_vote = Vote.objects.filter(**query_dict).first()
    
    def transaction():
        if not user_vote: #create vote for the first time
            query_dict['vote'] = vote
            Vote.objects.create(**query_dict)
            old_vote, new_vote = None, vote
        else:
            old_vote, new_vote = user_vote.vote, (vote if user_vote.vote != vote else 0)
            user_vote.vote = new_vote
            user_vote.save()

        content = get_unremoved_content(content, select_related=['user']) if isinstance(content, UUID) else content
        username = voter if isinstance(voter, str) else voter.username
        _distribute_scores(content, username, old_vote, new_vote)
        return None if new_vote == 0 else new_vote
    
    return transact(transaction, 'An error occured while voting the content')

def _distribute_scores(content: Content, voter: str, previous_vote: (int | None), final_vote: int):
    if content.user.username == voter: #self votes don't generate engagement or karma
        return
    
    is_comment = content.is_comment()
    added_karma, removed_karma = 0, 0
    
    delta_votes = final_vote if previous_vote is None else final_vote - previous_vote
    action_type = ActionType.VOTE_COMMENT if is_comment else ActionType.VOTE_POST
    owner_type = OwnerType.COMMENT_OWNER if is_comment else OwnerType.POST_OWNER
    
    if final_vote != 0:
        new_vote = VoteType.UPVOTE if final_vote == 1 else VoteType.DOWNVOTE
        added_karma = get_score(action_type, owner_type, ScoreType.KARMA)[new_vote.value]
    
    if previous_vote is not None and previous_vote != 0:
        old_vote = VoteType.UPVOTE if previous_vote == 1 else VoteType.DOWNVOTE
        removed_karma = get_score(action_type, owner_type, ScoreType.KARMA)[old_vote.value]
    
    delta_karma = added_karma - removed_karma
    User.objects.filter(username=content.user.username).update(karma = F('karma') + delta_karma)
    
    engagement_gained = get_score(action_type, owner_type, ScoreType.ENGAGEMENT_SCORE)
    activity_gained = get_score(action_type, OwnerType.ACTOR, ScoreType.ACTIVITY_SCORE)
    
    if is_comment:
        community_name = Community.objects.only('name').get(comments_id=content.id).name
    else:
        community_name = get_related_object(content, select_related=['community']).community.name
    
    query_dict = {}
    add_to_query_dict(query_dict, 'user', voter)
    add_to_query_dict(query_dict, 'community', community_name)
    
    membership = Membership.objects.filter(**query_dict).first()
    if membership is None:
        query_dict['role'] = GUEST
        query_dict['activity_score'] = activity_gained
        Membership.objects.create(**query_dict)
    else:
        if permission_granted(MEMBER, membership.role):
            activity_gained *= 2
            
        Membership.objects.filter(**query_dict).update(activity_score = F('activity_score') + activity_gained)
    
    if previous_vote is not None:
        Content.objects.filter(id=content.id).update(total_votes = F('total_votes') + delta_votes)
        return
    
    (Content.objects.filter(id=content.id)
     .update(total_votes = F('total_votes') + delta_votes,
             engagement_score = F('engagement_score') + engagement_gained))
    
    if is_comment:
        engagement_gained = get_score(ActionType.VOTE_COMMENT, OwnerType.POST_OWNER, ScoreType.ENGAGEMENT_SCORE)
        post = get_related_object(content, select_related=['post', 'post__content']).post.content
        Content.objects.filter(id=post.id).update(engagement_score = F('engagement_score') + engagement_gained)