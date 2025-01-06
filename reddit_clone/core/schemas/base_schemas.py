import graphene

from core.schemas.user_schemas import UserQuery, UserMutation
from core.schemas.post_schemas import PostQuery, PostMutation

class Query(UserQuery, PostQuery, graphene.ObjectType):
    pass

class Mutation(UserMutation, PostMutation, graphene.ObjectType):
    pass
    
schema = graphene.Schema(query=Query, mutation=Mutation)