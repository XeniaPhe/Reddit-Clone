import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.auth.auth import optional_authentication
from core.auth.roles import GUEST, MEMBER, MODERATOR, FOUNDER, ADMIN

from core.models import Content
from core.services.content_service import get_user_vote

class VoteEnum(graphene.Enum):
    UPVOTE = 1
    DOWNVOTE = -1

class ContentType(DjangoObjectType):
    class Meta:
        model = Content
        fields = ('id', 'body', 'publish_date',)
    
    class FilterMeta:
        filter_fields = {
            'id': ops.ID_OPERATORS,
            'body': ops.STRING_OPERATORS,
            'publish_date': ops.DATE_OPERATORS,
        }
        
    user_vote = graphene.Field(VoteEnum)
    
    @optional_authentication
    def resolve_user_vote(root, info, *args, **kwargs):
        user = info.context.user
        return None if not user.is_authenticated else get_user_vote(root.id, user.username)
        
class CommunityRoleEnum(graphene.Enum):
    GUEST = GUEST
    MEMBER = MEMBER
    MODERATOR = MODERATOR
    FOUNDER = FOUNDER
    ADMIN = ADMIN