import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.models import Community, Membership
from core.services.user_service import fetch_user, get_user, assert_user_exists
from core.services.community_service import get_community, create_community
from core.services.post_service import get_post
from core.services.comment_service import get_comment

from core.custom_errors import not_found
from core.utils.query_utils import get_list, filter_and_paginate
from core.auth.roles import DB_ROLE_CHOICES, CommunityRoleEnum, FOUNDER
from core.auth.auth import require_authentication, require_community_authorization

class CommunityType(DjangoObjectType):
    class Meta:
        model = Community
        fields = ('name', 'desc', 'created_at',)
        filter_fields = {
            'name': ops.ID_OPERATORS,
            'desc': ops.STRING_OPERATORS,
            'created_at': ops.DATE_OPERATORS,
        }

class CommunityQuery(graphene.ObjectType):
    community_by_name = graphene.Field(CommunityType, name=graphene.Argument(graphene.String, required=True))
    communities = get_list(CommunityType, filter=True, paginate=True,
                     of_user=graphene.Argument(graphene.String, required=False))
    
    def resolve_community_by_name(root, info, name):
        return get_community(name=name)
    
    def resolve_communities(root, info, of_user=None):
        if not of_user:
            return Community.objects.all()
        
        assert_user_exists(of_user)
        return Community.objects.filter(users__username=of_user)
    
class CreateCommunity(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=False)
        
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, name, description=None):
        user = info.context.user
        description = description if description else f'Welcome to {name}!'
        create_community(user, name, description)
        return CreateCommunity(success=True)
    
class UpdateCommunity(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        updated_description = graphene.String(required=False)
        
    success = graphene.Field(graphene.Boolean)
    
    @require_community_authorization('name', required_role=FOUNDER, admin_override=False)
    @require_authentication()
    def mutate(root, info, name, updated_description=None):
        community = get_community(name)
        if updated_description:
            community.desc = updated_description
            community.save()
        
        return UpdateCommunity(success=True)
    
class DeleteCommunity(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        
    success = graphene.Field(graphene.Boolean)
    
    @require_community_authorization('name', required_role=FOUNDER, admin_override=True)
    @require_authentication()
    def mutate(root, info, name):
        community = get_community(name)
        community.delete()
        return DeleteCommunity(success=True)
    
class CommunityMutation(graphene.ObjectType):
    create_community = CreateCommunity.Field()
    update_community = UpdateCommunity.Field()
    delete_community = DeleteCommunity.Field()