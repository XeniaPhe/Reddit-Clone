from django.db.models import F
from core.models import Community, User, Membership
from core.services.user_service import assert_user
from core.custom_errors import community_not_found, bad_request
from core.auth.roles import FOUNDER, MEMBER, MODERATOR, GUEST
from core.utils.service_utils import add_to_query_dict
from core.transact import transact
from core.utils.manager_utils import preselect

def get_community(name: str, select_related: list[str]=None, prefetch_related: list[str]=None):
    try:
        return preselect(Community, select_related, prefetch_related).get(name=name)
    except Community.DoesNotExist:
        community_not_found(name)

def assert_community_exists(name: str):
    get_community(name)

def create_community(user: (str | User), name: str, description: str):
    def transaction():
        community = Community.objects.create(name=name, desc=description)

        query_dict = { 'role': FOUNDER, }
        add_to_query_dict(query_dict, 'user', user)
        add_to_query_dict(query_dict, 'community', community)

        Membership.objects.create(**query_dict)
        return community
    
    return transact(transaction, 'An error occured while creating the community')

def join_or_leave_community(user: (str | User), community: (str | Community)) -> str:
    if not isinstance(community, Community):
        assert_community_exists(community)
    
    query_dict = {}
    add_to_query_dict(query_dict, 'user', user)
    add_to_query_dict(query_dict, 'community', community)
    membership = Membership.objects.filter(**query_dict).first()
    
    def transaction():
        if not membership:
            query_dict['role'] = MEMBER
            membership = Membership.objects.create(**query_dict)
        elif membership.role == FOUNDER:
            bad_request(f'Founder of a community cannot leave it')
        else:
            membership.role = MEMBER if membership.role == GUEST else GUEST
            membership.save()

        add = 1 if membership.role == MEMBER else -1
        community_name = community if isinstance(community, str) else community.name
        Community.objects.filter(name=community_name).update(number_of_members = F('number_of_members') + add)
        return membership.role
    
    return transact(transaction, 'An error occured while joining the community')

def promote_to_moderator(community: (str | Community), user: (str | User)):
    if not isinstance(user, User):
        assert_user(user)
        
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
    if not isinstance(user, User):
        assert_user(user)
        
    query_dict = {}
    add_to_query_dict(query_dict, 'user', user)
    add_to_query_dict(query_dict, 'community', community)
    membership = Membership.objects.filter(**query_dict).first()
    
    if membership and membership.role == MODERATOR:
        membership.role = MEMBER
        membership.save()
    else:
        bad_request('Only a moderator of a community can be demoted to member')