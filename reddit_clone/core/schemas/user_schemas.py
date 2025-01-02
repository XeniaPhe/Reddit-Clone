import graphene
from graphene_django import DjangoObjectType

from core.models import User
from core.custom_errors import not_found
from core.filters.filter import filtered_list, filter
import core.filters.operators as ops
from core.pagination import paginated_list, paginate
from core.utils.query_utils import get_list, filter_and_paginate
from core.auth.roles import DB_ROLE_CHOICES, CommunityRoleEnum
from core.auth.auth import require_authentication, create_jwt_token

from core.services import (
    get_user,
    get_user_with_email,
    assert_user_exists,
    get_community,
    assert_community_exists,
    get_post, get_comment)

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('username', 'email', 'join_date', 'score',)
        filter_fields = {
            'username': [ops.EXACT, ops.GT],
            'email': [ops.EXACT],
            'join_date': [ops.EXACT, ops.LT, ops.GT, ops.LTE, ops.GTE],
            'score': [ops.EXACT, ops.LT, ops.GT, ops.LTE, ops.GTE, ops.RANGE],
        }
    
    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(is_superuser=False)
    
class UserQuery(graphene.ObjectType):
    user_by_username = graphene.Field(UserType, username=graphene.Argument(graphene.String, required=True))
    user_by_post = graphene.Field(UserType, post_id=graphene.Argument(graphene.UUID, required=True))
    user_by_comment = graphene.Field(UserType, comment_id=graphene.Argument(graphene.UUID, required=True))
    users = get_list(UserType, filter=True, paginate=True,
                    community_name=graphene.Argument(graphene.String, required=False))
    
    user_role = graphene.Field(CommunityRoleEnum,
                               username=graphene.Argument(graphene.String, required=True),
                               community_name=graphene.Argument(graphene.String, required=True))
    
    def resolve_user_by_username(root, info, username):
        return get_user(username)
    
    def resolve_user_by_post(root, info, post_id):
        return get_post(post_id).user
    
    def resolve_user_by_comment(root, info, comment_id):
        return get_comment(comment_id).user
    
    @filter_and_paginate(UserType)
    def resolve_users(root, info, *args, **kwargs):
        community_name = kwargs.get('community_name', None)
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
    
class UserSignup(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        
    token = graphene.Field(graphene.String)
        
    @classmethod
    def mutate(cls, root, info, username, email, password):
        user = User.objects.create_user(username, email, password)
        token = create_jwt_token(user)
        return UserSignup(token=token)
    
class UserLogin(graphene.Mutation):
    class Arguments:
        username = graphene.String()
        password = graphene.String(required=True)
    
    token = graphene.Field(graphene.String)
    
    @classmethod
    def mutate(cls, root, info, username, password):
        user = None
        if User.objects.filter(username=username).exists():
            user = get_user(username)
        elif User.objects.filter(email=username).exists():
            user = get_user_with_email(username)
        else:
            not_found(f'Invalid username or password')
            
        if not user.check_password(password):
            not_found(f'Invalid username or password')
            
        token = create_jwt_token(user)
        return UserLogin(token=token)
        
class DeleteUser(graphene.Mutation):
    class Arguments:
        pass
    
    success = graphene.Field(graphene.Boolean)
    
    @classmethod
    @require_authentication(require_admin=False)
    def mutate(cls, root, info, *args, **kwargs):
        print(f"2:{info is None}")
        info.context.request.user.delete()
        return DeleteUser(success=True)
    
class UserMutation(graphene.ObjectType):
    user_signup = UserSignup.Field()
    user_login = UserLogin.Field()
    delete_user = DeleteUser.Field()