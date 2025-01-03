import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.models import Post
from core.schemas.content_type import ContentType
from core.custom_errors import not_found
from core.utils.query_utils import get_list, filter_and_paginate
from core.auth.roles import DB_ROLE_CHOICES, CommunityRoleEnum
from core.auth.auth import require_authentication, create_jwt_token

from core.services.user_service import assert_user_exists
from core.services.community_service import assert_community_exists
from core.services.post_service import get_post

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ('content', 'title', 'user', 'community',)
        filter_fields = {
            'content': ops.ID_OPERATORS,
            'title': ops.STRING_OPERATORS,
            'user': ops.ID_OPERATORS,
            'community': ops.ID_OPERATORS,
        }
        
class PostQuery(graphene.ObjectType):
    post_by_id = graphene.Field(PostType, id=graphene.Argument(graphene.UUID, required=True))
    posts = get_list(PostType, filter=True, paginate=True,
                     username=graphene.Argument(graphene.String, required=False),
                     community_name=graphene.Argument(graphene.String, required=False))
    
    def resolve_post_by_id(root, info, id):
        return get_post(id)
    
    @filter_and_paginate(PostType)
    def resolve_posts(root, info, *args, **kwargs):
        posts = Post.objects.all()
        username = kwargs.get('username', None)
        community_name = kwargs.get('community_name', None)
                
        if username:
            assert_user_exists(username)
            posts = posts = posts.filter(user__username=username)
        if community_name:
            assert_community_exists(community_name)
            posts = posts.filter(community__name=community_name)
            
        return posts
    
class CreatePost(graphene.Mutation):
    class Arguments:
        pass
    
class UpdatePost(graphene.Mutation):
    pass

class DeletePost(graphene.Mutation):
    pass
    
class PostMutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()