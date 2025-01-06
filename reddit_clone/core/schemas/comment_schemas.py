import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.models import Comment, Content
from core.schemas.content_type import ContentType
from core.services.user_service import assert_user_exists
from core.services.content_service import get_content, assert_content_exists
from core.services.post_service import assert_post_exists, get_post
from core.services.comment_service import get_comment, create_comment

from core.custom_errors import bad_request
from core.utils.query_utils import get_list, filter_and_paginate
from core.auth.roles import MEMBER
from core.auth.auth import require_authentication, require_community_authorization, require_content_authorization

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = ('content', 'parent', 'user', 'post',)
        filter_fields = {
            'content': ops.ID_OPERATORS,
            'parent': ops.ID_OPERATORS,
            'user': ops.ID_OPERATORS,
            'post': ops.ID_OPERATORS,
        }
        
class CommentQuery(graphene.ObjectType):
    comment_by_id = graphene.Field(CommentType, id=graphene.Argument(graphene.UUID, required=True))
    comments = get_list(CommentType, filter=True, paginate=True,
                     of_user=graphene.Argument(graphene.String, required=False),
                     of_post=graphene.Argument(graphene.UUID, required=False),
                     of_parent=graphene.Argument(graphene.UUID, required=False))
    
    def resolve_comment_by_id(root, info, id):
        return get_comment(id)
    
    @filter_and_paginate(CommentType)
    def resolve_comments(root, info, of_user=None, of_post=None, of_parent=None):
        if of_user:
            assert_user_exists(of_user)
            comments = Comment.objects.filter(user__username=of_user)
        if of_post:
            assert_post_exists(of_post)
            comments = comments.filter(post__id=of_post)
        if of_parent:
            assert_content_exists(of_parent)
            comments = comments.filter(parent__id=of_parent)
        
        return comments
    
class CreateComment(graphene.Mutation):
    class Arguments:
        community_name = graphene.String(required=True)
        post_id = graphene.UUID(required=True)
        parent_id = graphene.UUID(required=False)
        body = graphene.String(required=True)
        
    success = graphene.Field(graphene.Boolean)
    
    @require_community_authorization(community_param='community_name', required_role=MEMBER, admin_override=True)
    @require_authentication()
    def mutate(root, info, community_name, post_id, body, parent_id=None):
        user = info.context.user
        post = get_post(post_id)
        
        if post.community.name != community_name:
            bad_request('The post was shared in a different community than specified')
            
        parent = get_content(parent_id)
        create_comment(body, parent, user, post)
        return CreateComment(success=True)
                
    
class UpdateComment(graphene.Mutation):
    class Arguments:
        comment_id = graphene.UUID(required=True)
        updated_body = graphene.String(required=False)
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, comment_id, updated_body=None):
        user = info.context.user
        comment = require_content_authorization(user, comment_id, Content.ContentType.COMMENT, admin_override=False)
        
        if updated_body:
            comment.content.body = updated_body
            comment.save()
            
        return UpdateComment(success=True)
        
class DeleteComment(graphene.Mutation):
    class Arguments:
        comment_id = graphene.UUID(required=True)
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, comment_id):
        user = info.context.user
        comment = require_content_authorization(user, comment_id, Content.ContentType.COMMENT, admin_override=True)
        comment.delete()
        return DeleteComment(success=True)
    
class CommentMutation(graphene.ObjectType):
    create_comment = CreateComment.Field()
    update_comment = UpdateComment.Field()
    delete_comment = DeleteComment.Field()