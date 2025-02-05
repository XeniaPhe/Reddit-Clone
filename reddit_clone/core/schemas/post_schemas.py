import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, IntegerField
from django.db.models.functions import ExtractHour

import core.filters.operators as ops
from core.utils.query_utils import get_list, paginate
from core.auth.roles import MEMBER
from core.auth.auth import (
    require_authentication,
    require_community_authorization,
    require_content_authorization,
    optional_authentication,
    )

from core.models import Post
from core.services.community_service import assert_community_exists
from core.services.content_service import get_related_object
from core.services.post_service import get_post, create_post
from core.schemas.common import ContentType

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ('title', 'content', 'community',)

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
    
    hot_posts = get_list(PostType, filter=False, paginate=True,
                         community_name=graphene.Argument(graphene.String, required=True))
    
    top_posts = get_list(PostType, filter=False, paginate=True,
                         community_name=graphene.Argument(graphene.String, required=True),
                         time_range=graphene.Argument(TimeRangeEnum, required=False, default_value=TimeRangeEnum.PAST_24_HOURS))
    
    home_feed = get_list(PostType, filter=False, paginate=True)
    
    def resolve_post_by_id(root, info, id):
        return get_post(id, select_related=['content'])
    
    @optional_authentication
    @paginate()
    def resolve_posts(root, info, *args, **kwargs):
        return (Post.objects
                .select_related('content')
                .order_by('-content__publish_date')
                .all())
    
    @optional_authentication
    @paginate()
    def resolve_new_posts(root, info, community_name, *args, **kwargs):
        assert_community_exists(community_name)
        return (Post.objects
                .select_related('content')
                .filter(community_id=community_name)
                .order_by('-content__publish_date'))
        
    @optional_authentication
    @paginate()
    def resolve_hot_posts(root, info, community_name, *args, **kwargs):
        assert_community_exists(community_name)
        
        return (Post.objects
         .select_related('content')
         .filter(community_id=community_name)
         .annotate(
             hours_since_publish = ExpressionWrapper(
                 ExtractHour(timezone.now() - F('content__publish_date')),
                 output_field=IntegerField()
             )
         )
         .annotate(
             engagement_per_hour = ExpressionWrapper(
                 F('engagement_score') / F('hours_since_publish'),
                 output_field=IntegerField()
             )
         )
         .order_by('-engagement_per_hour'))
        
    @optional_authentication
    @paginate()
    def resolve_top_posts(root, info, community_name, time_range, *args, **kwargs):
        assert_community_exists(community_name)
        
        return (Post.objects
                .select_related('content')
                .filter(community_id=community_name)
                .order_by('-content__total_votes'))
        
    
        
class CreatePost(graphene.Mutation):
    class Arguments:
        community_name = graphene.String(required=True)
        title = graphene.String(required=True)
        body = graphene.String(required=False)
        
    post_id = graphene.Field(graphene.UUID)
    
    @require_authentication()
    @require_community_authorization(community_param='community_name', required_role=MEMBER, admin_override=True)
    def mutate(root, info, community_name, title, body=''):
        _, content = create_post(title, body, info.context.user, community_name)
        return CreatePost(post_id=content.id)
    
class UpdatePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.UUID(required=True)
        updated_title = graphene.String(required=False)
        updated_body = graphene.String(required=False)
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, post_id, updated_title=None, updated_body=None):
        content = require_content_authorization(info.context.user, post_id, check_deleted=True, admin_override=False)
        post = get_related_object(content)
        
        if updated_body:
            content.body = updated_body
            content.save()
        
        if updated_title:
            post.title = updated_title
            post.save()
            
        return UpdatePost(success=True)
        
class DeletePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.UUID(required=True)
    
    success = graphene.Field(graphene.Boolean)
    
    @require_authentication()
    def mutate(root, info, post_id):
        content = require_content_authorization(info.context.user, post_id, check_deleted=True, admin_override=True)
        content.deleted = True
        content.save()
        return DeletePost(success=True)
    
class PostMutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()