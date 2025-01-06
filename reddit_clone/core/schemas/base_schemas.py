import graphene

from core.schemas.user_schemas import UserQuery, UserMutation
from core.schemas.post_schemas import PostQuery, PostMutation
from core.schemas.community_schemas import CommunityQuery, CommunityMutation

class Query(UserQuery, PostQuery, CommunityQuery, graphene.ObjectType):
    pass

class Mutation(UserMutation, PostMutation, CommunityMutation, graphene.ObjectType):
    pass
    
schema = graphene.Schema(query=Query, mutation=Mutation)