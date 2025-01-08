from core.models import Community, User, Membership
from core.custom_errors import community_not_found, bad_request
from core.auth.roles import FOUNDER, MEMBER, MODERATOR, GUEST

def get_community(name: str) -> Community | None:
    try:
        return Community.objects.get(name=name)
    except Community.DoesNotExist:
        community_not_found(name)
        
def assert_community_exists(name: str):
    get_community(name)
    
def create_community(user: User, name: str, description: str):
    community = Community.objects.create(name=name, desc=description)
    Membership.objects.create(role=FOUNDER, user=user, community=community)
    return community

def join_or_leave_community(user: User, community: Community) -> str:
    membership = Membership.objects.filter(user_id=user.username, community_id=community.name).first()
    
    if not membership:
        Membership.objects.create(role=MEMBER, user=user, community=community)
        return MEMBER
    
    if membership.role == FOUNDER:
        bad_request(f'Founder "{user.username}" of the community "{community.name}" cannot leave it')
    
    membership.role = MEMBER if membership.role == GUEST else GUEST
    membership.save()
    return membership.role

def promote_to_moderator(community: Community, user: User):
    membership = Membership.objects.filter(user_id=user.username, community_id=community.name).first()
    
    if membership and membership.role == MEMBER:
        membership.role = MODERATOR
        membership.save()
    else:
        bad_request('Only a member of a community can be promoted to moderator')
        
def demote_to_member(community: Community, user: User):
    membership = Membership.objects.filter(user_id=user.username, community_id=community.name).first()
    
    if membership and membership.role == MODERATOR:
        membership.role = MEMBER
        membership.save()
    else:
        bad_request('Only a moderator of a community can be demoted to member')