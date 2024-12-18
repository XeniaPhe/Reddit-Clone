import graphene
from graphene_django import DjangoObjectType
from core.models import *

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('username', 'email', 'join_date', 'score')
        
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

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    communities = graphene.List(CommunityType)
    posts_by_community = graphene.List(PostType)
    comments_by_post = graphene.List(CommentType)
    
    def resolve_users(root, info):
        return User.objects.all()

    def resolve_communities(root, info):
        return Community.objects.all()
    
    def resolve_posts_by_community(root, info, community):
        return Community.objects.filter(name=community)

    def resolve_comments_by_post(root, info, post):
        return Comment.objects.filter(post__id=post)
    
schema = graphene.Schema(query=Query)