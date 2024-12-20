import graphene
from graphene_django import DjangoObjectType

from core.models import User, Post, Comment
from core.auth.auth import require_jwt
from core.auth.roles import DB_ROLE_CHOICES, CommunityRoleEnum
from core.services import get_user, assert_user_exists, get_community, assert_community_exists, get_post, get_comment

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('username', 'email', 'join_date', 'score')
    
    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(is_superuser=False)
        
class UserQuery(graphene.ObjectType):
    user_by_username = graphene.Field(UserType, username=graphene.Argument(graphene.String, required=True))
    user_by_post = graphene.Field(UserType, post_id=graphene.Argument(graphene.UUID, required=True))
    user_by_comment = graphene.Field(UserType, comment_id=graphene.Argument(graphene.UUID, required=True))
    users = graphene.List(UserType, community_name=graphene.Argument(graphene.String, required=False))
    
    user_role = graphene.Field(CommunityRoleEnum,
                               username=graphene.Argument(graphene.String, required=True),
                               community_name=graphene.Argument(graphene.String, required=True))
    
    def resolve_user_by_username(root, info, username):
        return get_user(username)
    
    def resolve_user_by_post(root, info, post_id):
        return get_post(id).user
    
    def resolve_user_by_comment(root, info, comment_id):
        return get_comment(id).user
        
    def resolve_users(root, info, community_name=None):
        if community_name is None:
            return User.objects.all()
        
        assert_community_exists(community_name)
        return User.objects.filter(memberships__community__name=community_name)
    
    def resolve_user_role(root, info, username, community_name):
        assert_user_exists(username)
        community = get_community(community_name)
        membership = community.memberships.filter(user__username=username)
        
        if not membership.exists():
            return CommunityRoleEnum.GUEST
        
        return CommunityRoleEnum(DB_ROLE_CHOICES[membership.first().role])