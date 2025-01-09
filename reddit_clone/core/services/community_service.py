from core.models import Community, User, Membership
from core.custom_errors import community_not_found, bad_request
from core.auth.roles import FOUNDER, MEMBER, MODERATOR, GUEST
from core.utils.service_utils import add_to_query_dict

def get_community(name: str) -> Community | None:
    try:
        return Community.objects.get(name=name)
    except Community.DoesNotExist:
        community_not_found(name)
        
def assert_community_exists(name: str):
    assert Community.objects.filter(name=name).exists(), f'Community "{name}" does not exist'

def create_community(user: (str | User), name: str, description: str):
    community = Community.objects.create(name=name, desc=description)
    
    query_dict = { 'role': FOUNDER, }
    add_to_query_dict(query_dict, 'user', user)
    add_to_query_dict(query_dict, 'community', community)
    
    Membership.objects.create(**query_dict)
    return community

def join_or_leave_community(user: (str | User), community: (str | Community)) -> str:
    query_dict = {}
    add_to_query_dict(query_dict, 'user', user)
    add_to_query_dict(query_dict, 'community', community)
    membership = Membership.objects.filter(**query_dict).first()
    
    if not membership:
        query_dict['role'] = MEMBER
        Membership.objects.create(**query_dict)
        return MEMBER
    
    if membership.role == FOUNDER:
        bad_request(f'Founder of a community cannot leave it')
    
    membership.role = MEMBER if membership.role == GUEST else GUEST
    membership.save()
    return membership.role

def promote_to_moderator(community: (str | Community), user: (str | User)):
    query_dict = {}
    add_to_query_dict(query_dict, 'user', user)
    add_to_query_dict(query_dict, 'community', community)
    membership = Membership.objects.filter(**query_dict).first()
    
    if membership and membership.role == MEMBER:
        membership.role = MODERATOR
        membership.save()
    else:
        bad_request('Only a member of a community can be promoted to moderator')
        
def demote_to_member(community: (str | Community), user: (str | User)):
    query_dict = {}
    add_to_query_dict(query_dict, 'user', user)
    add_to_query_dict(query_dict, 'community', community)
    membership = Membership.objects.filter(**query_dict).first()
    
    if membership and membership.role == MODERATOR:
        membership.role = MEMBER
        membership.save()
    else:
        bad_request('Only a moderator of a community can be demoted to member')