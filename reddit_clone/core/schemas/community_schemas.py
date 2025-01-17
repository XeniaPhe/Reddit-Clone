import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.utils.query_utils import get_list, filter_and_paginate
from core.auth.roles import FOUNDER
from core.auth.auth import require_authentication, require_community_authorization

from core.models import Community
from core.services.user_service import assert_user
from core.services.community_service import (
    get_community,
    create_community,
    promote_to_moderator,
    demote_to_member,
)

class CommunityType(DjangoObjectType):
    class Meta:
        model = Community
        fields = ('name', 'desc', 'created_at',)
        
    class FilterMeta:
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
    
    @filter_and_paginate(CommunityType)
    def resolve_communities(root, info, of_user=None, *args, **kwargs):
        if not of_user:
            return Community.objects.all()
        
        assert_user(of_user)
        return Community.objects.filter(users_id=of_user)
    
class CreateCommunity(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=False)
        
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, name, description=None):
        description = description if description else f'Welcome to {name}!'
        create_community(info.context.user, name, description)
        return CreateCommunity(success=True)
    
class UpdateCommunity(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        updated_description = graphene.String(required=False)
        
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    @require_community_authorization('name', required_role=FOUNDER, admin_override=False)
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
    
    @require_authentication()
    @require_community_authorization('name', required_role=FOUNDER, admin_override=True)
    def mutate(root, info, name):
        get_community(name).delete()
        return DeleteCommunity(success=True)

class PromoteToModerator(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        community_name = graphene.String(required=True)
        
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    @require_community_authorization(community_param='community_name', required_role=FOUNDER, admin_override=False)
    def mutate(root, info, username, community_name, *args, **kwargs):
        promote_to_moderator(community_name, username)
        return PromoteToModerator(success=True)
    
class DemoteToMember(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        community_name = graphene.String(required=True)
        
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    @require_community_authorization(community_param='community_name', required_role=FOUNDER, admin_override=False)
    def mutate(root, info, username, community_name, *args, **kwargs):
        demote_to_member(community_name, username)
        return DemoteToMember(success=True)

class CommunityMutation(graphene.ObjectType):
    create_community = CreateCommunity.Field()
    update_community = UpdateCommunity.Field()
    delete_community = DeleteCommunity.Field()
    promote_to_moderator = PromoteToModerator.Field()
    demote_to_member = DemoteToMember.Field()