from uuid import UUID
from core.models import Content, User, Comment, Post, Vote
from core.custom_errors import content_not_found

def get_content(id: UUID):
    try:
        return Content.objects.get(id=id)
    except Content.DoesNotExist:
        content_not_found(id)
        
def assert_content_exists(id: UUID):
    get_content(id)

def get_related_object(content: Content):
    manager = Post.objects if content.is_post() else Comment.objects
    return manager.get(id=content.id)

def _to_vote_or_none(from_vote:int):
    return None if from_vote == 0 else from_vote

def vote_content(id: UUID, user: User, vote: int) -> int:
    content = get_content(id)
    user_vote = content.votes.filter(user_id=user.username)
    
    if not user_vote.exists():
        user_vote = Vote.objects.create(user=user, content=content, vote=vote)
        return vote
    
    current_vote = user_vote.first()
    current_vote.vote = vote if current_vote.vote != vote else 0
    current_vote.save()
    return _to_vote_or_none(current_vote.vote)

def get_user_vote(content_id: UUID, username: str):
    vote = Vote.objects.filter(content_id=content_id, user_id=username).only('vote').first()
    return None if not vote else _to_vote_or_none(vote.vote)