import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.utils.query_utils import get_list, filter_and_paginate
from core.auth.roles import MEMBER
from core.auth.auth import (
    require_authentication,
    require_community_authorization,
    require_content_authorization,
    optional_authentication,
    )

from core.models import Post, Content
from core.services.community_service import assert_community_exists
from core.services.post_service import get_post, create_post
from core.schemas.common import ContentType

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ('content', 'title', 'community',)

    class FilterMeta:
        filter_fields = {
            'content': ops.ID_OPERATORS,
            'title': ops.STRING_OPERATORS,
            'community': ops.ID_OPERATORS,
        }

class TimeRangeEnum(graphene.Enum):
    PAST_HOUR = 0
    PAST_24_HOURS = 1
    PAST_WEEK = 2
    PAST_MONTH = 3
    PAST_QUARTER = 4
    PAST_YEAR = 5
    ALL_TIME = 6
    
class PostQuery(graphene.ObjectType):
    post_by_id = graphene.Field(PostType, id=graphene.Argument(graphene.UUID, required=True))
    posts = get_list(PostType, filter=True, paginate=True)
    
    new_posts = get_list(PostType, filter=False, paginate=True,
                         community_name=graphene.Argument(graphene.String, required=True))
    
    top_posts = get_list(PostType, filter=False, paginate=True,
                         community_name=graphene.Argument(graphene.String, required=True),
                         time_range=graphene.Argument(TimeRangeEnum, required=False, default_value=TimeRangeEnum.PAST_24_HOURS))
    
    hot_posts = get_list(PostType, filter=False, paginate=True,
                         community_name=graphene.Argument(graphene.String, required=True),
                         time_range=graphene.Argument(TimeRangeEnum, required=False, default_value=TimeRangeEnum.PAST_24_HOURS))
    
    def resolve_post_by_id(root, info, id):
        return get_post(id)
    
    @optional_authentication
    @filter_and_paginate(PostType)
    def resolve_posts(root, info, *args, **kwargs):
        return Post.objects.all()
        
class CreatePost(graphene.Mutation):
    class Arguments:
        community_name = graphene.String(required=True)
        title = graphene.String(required=True)
        body = graphene.String(required=False)
        
    post_id = graphene.Field(graphene.UUID)
    
    @require_authentication()
    @require_community_authorization(community_param='community_name', required_role=MEMBER, admin_override=True)
    def mutate(root, info, community_name, title, body=''):
        assert_community_exists(community_name)
        post = create_post(title, body, info.context.user, community_name)
        return CreatePost(post_id=post.content.id)
    
class UpdatePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.UUID(required=True)
        updated_title = graphene.String(required=False)
        updated_body = graphene.String(required=False)
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, post_id, updated_title=None, updated_body=None):
        post = require_content_authorization(info.context.user, post_id, admin_override=False)
        update = False
        
        if updated_title:
            post.title = updated_title
            update = True
        
        if updated_body:
            post.content.body = updated_body
            update = True
            
        if update:
            post.save()
        
        return UpdatePost(success=True)
        
class DeletePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.UUID(required=True)
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, post_id):
        post = require_content_authorization(info.context.user, post_id, admin_override=True)
        post.content.delete()
        return DeletePost(success=True)
    
class PostMutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()