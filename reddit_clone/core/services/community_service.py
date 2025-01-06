from core.models import Community, User, Membership
from core.custom_errors import community_not_found
from core.auth.roles import FOUNDER, MEMBER, MODERATOR

def get_community(name: str) -> Community | None:
    try:
        return Community.objects.get(name=name)
    except Community.DoesNotExist:
        community_not_found(name)
        
def assert_community_exists(name: str):
    get_community(name)
    
def create_community(user: User, name: str, description: str):
    community = Community.objects.create(name=name, description=description)
    Membership.objects.create(role=FOUNDER, user=user, community=community)
    return community

def join_community(user: User, community: Community, with_role=MEMBER):
    Membership.objects.create(role=with_role, user=user, community=community)
    
def promote_to_moderator(community: Community, user: User):
    membership = Membership.objects.filter(user__username=user.username, community__name=community.name).first()
    
    if membership.exists():
        membership.first().role = MODERATOR
    else:
        join_community(user, community, MODERATOR)