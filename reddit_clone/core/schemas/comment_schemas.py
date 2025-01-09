import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.custom_errors import bad_request
from core.utils.query_utils import get_list, filter_and_paginate
from core.auth.roles import MEMBER
from core.auth.auth import require_authentication, require_community_authorization, require_content_authorization

from core.models import Comment, Content
from core.services.post_service import get_post
from core.services.comment_service import get_comment, create_comment
from core.schemas.common import ContentType

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = ('content', 'parent', 'post',)
        
    class FilterMeta:
        filter_fields = {
            'content': ops.ID_OPERATORS,
            'parent': ops.ID_OPERATORS,
            'post': ops.ID_OPERATORS,
        }
        
class CommentQuery(graphene.ObjectType):
    comment_by_id = graphene.Field(CommentType, id=graphene.Argument(graphene.UUID, required=True))
    comments = get_list(CommentType, filter=True, paginate=True)
    
    def resolve_comment_by_id(root, info, id):
        return get_comment(id)
    
    @filter_and_paginate(CommentType)
    def resolve_comments(root, info, *args, **kwargs):
        return Comment.objects.all()
    
class CreateComment(graphene.Mutation):
    class Arguments:
        community_name = graphene.String(required=True)
        post_id = graphene.UUID(required=True)
        parent_id = graphene.UUID(required=False)
        body = graphene.String(required=True)
        
    comment_id = graphene.Field(graphene.UUID)
    
    @require_authentication()
    @require_community_authorization(community_param='community_name', required_role=MEMBER, admin_override=True)
    def mutate(root, info, community_name, post_id, body, parent_id=None):
        post = get_post(post_id)
        
        if post.community.name != community_name:
            bad_request('The post was shared in a different community than specified')
        
        parent_id = post_id if not parent_id else parent_id
        comment = create_comment(body, parent_id, info.context.user, post)
        return CreateComment(comment_id = comment.content.id)
                
class UpdateComment(graphene.Mutation):
    class Arguments:
        comment_id = graphene.UUID(required=True)
        updated_body = graphene.String(required=False)
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, comment_id, updated_body=None):
        comment = require_content_authorization(info.context.user, comment_id, admin_override=False)
        
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
        comment = require_content_authorization(info.context.user, comment_id, admin_override=True)
        comment.content.delete()
        return DeleteComment(success=True)
    
class CommentMutation(graphene.ObjectType):
    create_comment = CreateComment.Field()
    update_comment = UpdateComment.Field()
    delete_comment = DeleteComment.Field()