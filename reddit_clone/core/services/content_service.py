from uuid import UUID
from django.db.models import F
from core.models import Content, User, Comment, Post, Vote
from core.custom_errors import content_not_found
from core.utils.service_utils import add_to_query_dict

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

def vote_content(content: (UUID | Content), user: (str | User), vote: int) -> int:
    if not isinstance(content, Content):
        assert_content_exists(content)
    
    query_dict = {}
    add_to_query_dict(query_dict, 'content', content)
    add_to_query_dict(query_dict, 'user', user)
    
    user_vote = Vote.objects.filter(**query_dict).first()
    
    if not user_vote:
        query_dict['vote'] = vote
        Vote.objects.create(**query_dict)
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
        
def get_user_vote(content: (UUID | Content), user: (str | User)):
    query_dict = {}
    add_to_query_dict(query_dict, 'content', content)
    add_to_query_dict(query_dict, 'user', user)
    
    vote = Vote.objects.filter(**query_dict).only('vote').first()
    return None if not vote else vote.vote