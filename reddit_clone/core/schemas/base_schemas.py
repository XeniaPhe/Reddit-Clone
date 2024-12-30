import graphene

from core.schemas.user_schemas import UserQuery

class Query(UserQuery, graphene.ObjectType):
    pass
    
schema = graphene.Schema(query=Query)