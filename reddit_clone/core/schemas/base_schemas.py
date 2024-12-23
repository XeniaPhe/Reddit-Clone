import graphene
from graphene_django import DjangoObjectType

from core.models import *
from core.schemas.user_schemas import UserQuery

class CommunityType(DjangoObjectType):
    class Meta:
        model = Community
        fields = ('name', 'description')

class MembershipType(DjangoObjectType):
    class Meta:
        model = Membership
        fields = ('role', 'user', 'community')

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ('id', 'title', 'body', 'publish_date', 'user', 'community')

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = ('id', 'body', 'publish_date', 'user', 'parent', 'post')

class Query(UserQuery, graphene.ObjectType):
    pass
    
schema = graphene.Schema(query=Query)