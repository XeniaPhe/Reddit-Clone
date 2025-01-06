import graphene

from core.schemas.user_schemas import UserQuery, UserMutation
from core.schemas.community_schemas import CommunityQuery, CommunityMutation
from core.schemas.post_schemas import PostQuery, PostMutation
from core.schemas.comment_schemas import CommentQuery, CommentMutation

class Query(UserQuery, CommunityQuery, PostQuery, CommentQuery, graphene.ObjectType):
    pass

class Mutation(UserMutation, CommunityMutation, PostMutation, CommentMutation, graphene.ObjectType):
    pass
    
schema = graphene.Schema(query=Query, mutation=Mutation)