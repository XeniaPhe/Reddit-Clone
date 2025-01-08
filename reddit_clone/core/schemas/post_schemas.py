import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.utils.query_utils import get_list, filter_and_paginate
from core.auth.roles import MEMBER
from core.auth.auth import require_authentication, require_community_authorization, require_content_authorization

from core.models import Post, Content
from core.schemas.content_type import ContentType
from core.services.community_service import get_community
from core.services.post_service import get_post, create_post

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ('content', 'title', 'user', 'community',)

    class FilterMeta:
        filter_fields = {
            'content': ops.ID_OPERATORS,
            'title': ops.STRING_OPERATORS,
            'user': ops.ID_OPERATORS,
            'community': ops.ID_OPERATORS,
        }
        
class PostQuery(graphene.ObjectType):
    post_by_id = graphene.Field(PostType, id=graphene.Argument(graphene.UUID, required=True))
    posts = get_list(PostType, filter=True, paginate=True)
    
    def resolve_post_by_id(root, info, id):
        return get_post(id)
    
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
        user = info.context.user
        community = get_community(community_name)
        post = create_post(title, body, user, community)
        return CreatePost(post_id=post.content.id)
    
class UpdatePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.UUID(required=True)
        updated_title = graphene.String(required=False)
        updated_body = graphene.String(required=False)
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, post_id, updated_title=None, updated_body=None):
        user = info.context.user
        post = require_content_authorization(user, post_id, Content.ContentType.POST, admin_override=False)
        
        if updated_title:
            post.title = updated_title
        
        if updated_body:
            post.content.body = updated_body
        
        post.save()
        return UpdatePost(success=True)
        
class DeletePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.UUID(required=True)
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, post_id):
        user = info.context.user
        post = require_content_authorization(user, post_id, Content.ContentType.POST, admin_override=True)
        post.content.delete()
        return DeletePost(success=True)
    
class PostMutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()