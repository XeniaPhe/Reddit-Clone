import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.custom_errors import not_found
from core.utils.query_utils import get_list, filter_and_paginate
from core.auth.roles import GUEST
from core.auth.auth import require_authentication, create_jwt_token

from core.models import User, Membership
from core.services.user_service import fetch_user, get_user, assert_user_exists
from core.services.community_service import get_community, assert_community_exists, join_or_leave_community
from core.services.content_service import vote_content
from core.schemas.common import VoteEnum, CommunityRoleEnum

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('username', 'email', 'join_date', 'karma',)
        
    class FilterMeta:
        filter_fields = {
            'username': ops.ID_OPERATORS,
            'email': (ops.EXACT,),
            'join_date': ops.DATE_OPERATORS,
            'karma': ops.NUMERIC_OPERATORS,
        }
        
    admin = graphene.Boolean()
    
    def resolve_admin(root, info):
        return root.is_superuser
    
    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(is_superuser=False)
    
class UserQuery(graphene.ObjectType):
    user_by_username = graphene.Field(UserType, username=graphene.Argument(graphene.String, required=True))
    users = get_list(UserType, filter=True, paginate=True,
                    of_community=graphene.Argument(graphene.String, required=False))
    
    user_role = graphene.Field(CommunityRoleEnum,
                               of_user=graphene.Argument(graphene.String, required=True),
                               in_community=graphene.Argument(graphene.String, required=True))
    
    def resolve_user_by_username(root, info, username):
        return get_user(username)
    
    @filter_and_paginate(UserType)
    def resolve_users(root, info, of_community=None, *args, **kwargs):
        if not of_community:
            return User.objects.all()
        
        assert_community_exists(of_community)
        return User.objects.filter(communities_id=of_community)
    
    def resolve_user_role(root, info, of_user, in_community):
        assert_user_exists(of_user)
        assert_community_exists(in_community)
        membership = Membership.objects.filter(user_id=of_user, community_id=in_community).first()
        return GUEST if not membership else membership.role
    
class UserSignup(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        
    token = graphene.Field(graphene.String)
        
    def mutate(root, info, username, email, password):
        user = User.objects.create_user(username, email, password)
        token = create_jwt_token(user)
        return UserSignup(token=token)
    
class UserSignin(graphene.Mutation):
    class Arguments:
        username_or_email = graphene.String(required=True)
        password = graphene.String(required=True)
    
    token = graphene.Field(graphene.String)
    
    def mutate(root, info, username_or_email, password):
        user = fetch_user(username_or_email, 'Invalid username or password')
        if not user.check_password(password):
            not_found(f'Invalid username or password')
            
        token = create_jwt_token(user)
        return UserSignin(token=token)
        
class DeleteUser(graphene.Mutation):
    class Arguments:
        pass
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, *args, **kwargs):
        info.context.user.delete()
        return DeleteUser(success=True)

class AlterCommunityMembership(graphene.Mutation):
    class Arguments:
        community_name = graphene.String(required=True)
        pass
    
    final_user_role = graphene.Field(CommunityRoleEnum)
    
    @require_authentication()
    def mutate(root, info, community_name, *args, **kwargs):
        user = info.context.user
        community = get_community(community_name)
        final_user_role = join_or_leave_community(user, community)
        return AlterCommunityMembership(final_user_role=final_user_role)
    
class VoteContent(graphene.Mutation):
    class Arguments:
        content_id = graphene.UUID(required=True)
        vote = graphene.Argument(VoteEnum, required=True)
    
    final_vote = graphene.Field(VoteEnum)
    
    @require_authentication()
    def mutate(root, info, content_id, vote, *args, **kwargs):
        user = info.context.user
        final_vote = vote_content(content_id, user, vote.value)
        return VoteContent(final_vote=final_vote)
        
class UserMutation(graphene.ObjectType):
    user_signup = UserSignup.Field()
    user_signin = UserSignin.Field()
    delete_user = DeleteUser.Field()
    alter_community_membership = AlterCommunityMembership.Field()
    vote_content = VoteContent.Field()