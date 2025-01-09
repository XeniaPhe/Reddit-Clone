from uuid import UUID
from django.db.models import F
from core.models import Content, User, Comment, Post, Vote
from core.custom_errors import content_not_found

def get_content(id: UUID):
    try:
        return Content.objects.get(id=id)
    except Content.DoesNotExist:
        content_not_found(id)
        
def assert_content_exists(id: UUID):
    assert Content.objects.filter(id=id).exists(), f'Content with ID "{id}" does not exist'

def get_related_object(content: Content):
    manager = Post.objects if content.is_post() else Comment.objects
    return manager.get(id=content.id)

def vote_content(id: UUID, user: User, vote: int) -> int:
    assert_content_exists(id)
    user_vote = Vote.objects.filter(user_id=user.username, content_id=id).first()
    
    if not user_vote:
        Vote.objects.create(user=user, content_id=id, vote=vote)
        add, ret = vote, vote
    elif user_vote.vote == vote:
        user_vote.delete()
        add, ret = -vote, None
    else:
        user_vote.vote = vote
        user_vote.save()
        add, ret = vote * 2, vote
        
    Content.objects.filter(id=id).update(total_votes=F('total_votes') + add)
    return ret
        
def get_user_vote(content_id: UUID, username: str):
    vote = Vote.objects.filter(content_id=content_id, user_id=username).only('vote').first()
    return None if not vote else vote.vote