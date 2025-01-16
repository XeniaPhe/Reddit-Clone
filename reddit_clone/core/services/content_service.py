from uuid import UUID
from django.db.models import F
from core.models import Content, User, Comment, Post, Vote
from core.custom_errors import content_not_found, content_deleted
from core.services.score_service import VoteType, ActionType, ScoreType, ContentType, get_score
from core.utils.service_utils import add_to_query_dict

def get_content(id: UUID):
    try:
        return Content.objects.get(id=id)
    except Content.DoesNotExist:
        content_not_found(id)
        
def get_unremoved_content(id: UUID):
    content = get_content(id)
    if content.deleted:
        content_deleted(id)
        
    return content
        
def assert_content_exists(id: UUID):
    get_content(id)
    
def assert_content(id: UUID):
    get_unremoved_content(id)

def get_related_object(content: Content):
    manager = Post.objects if content.is_post() else Comment.objects
    return manager.get(id=content.id)

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
    
    if not user_vote: #create vote for the first time
        query_dict['vote'] = vote
        Vote.objects.create(**query_dict)
        old_vote, new_vote = None, vote
    else:
        old_vote, new_vote = user_vote.vote, (vote if user_vote.vote != vote else 0)
        user_vote.vote = new_vote
        user_vote.save()
    
    content = get_unremoved_content(content) if isinstance(content, UUID) else content
    username = voter if isinstance(voter, str) else voter.username
    _distribute_scores(content, username, old_vote, new_vote)
    return None if new_vote == 0 else new_vote

def _distribute_scores(content: Content, voter: str, previous_vote: (int | None), final_vote: int):
    if content.user.username == voter: #self votes don't generate engagement or karma
        return
    
    added_karma, removed_karma = 0, 0
    delta_votes = final_vote if previous_vote is None else final_vote - previous_vote
    action_type = ActionType.VOTE_COMMENT if content.is_comment() else ActionType.VOTE_POST
    content_type = ContentType.COMMENT if content.is_comment() else ContentType.POST
    
    if final_vote != 0:
        new_vote = VoteType.UPVOTE if final_vote == 1 else VoteType.DOWNVOTE
        added_karma = get_score(action_type, content_type, ScoreType.KARMA, vote = new_vote)
    
    if previous_vote is not None and previous_vote != 0:
        old_vote = VoteType.UPVOTE if previous_vote == 1 else VoteType.DOWNVOTE
        removed_karma = get_score(action_type, content_type, ScoreType.KARMA, vote = old_vote)
    
    delta_karma = added_karma - removed_karma
    User.objects.filter(username=content.user.username).update(karma=F('karma') + delta_karma)
    
    if previous_vote is not None: #do not update engagement if it's not the first time the user voted this content
        Content.objects.filter(id=content.id).update(total_votes = F('total_votes') + delta_votes)
    elif content.is_comment():
        score = get_score(ActionType.VOTE_COMMENT, ContentType.COMMENT, ScoreType.ENGAGEMENT_SCORE, order_index=0)
        (Content.objects.filter(id=content.id)
         .update(engagement_score = F('engagement_score') + score, total_votes = F('total_votes') + delta_votes))
        
        for i in range(1, 4):
            content = get_related_object(content).parent
            if content.is_post():
                break
            
            score = get_score(ActionType.VOTE_COMMENT, ContentType.COMMENT, ScoreType.ENGAGEMENT_SCORE, order_index=i)
            Content.objects.filter(id=content.id).update(engagement_score = F('engagement_score') + score)
    else:
        score = get_score(ActionType.VOTE_POST, ContentType.POST, ScoreType.ENGAGEMENT_SCORE)
        (Content.objects.filter(id=content.id)
         .update(engagement_score = F('engagement_score') + score, total_votes = F('total_votes') + delta_votes))