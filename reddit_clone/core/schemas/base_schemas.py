import graphene

from core.schemas.user_schemas import UserQuery, TestQuery

class Query(TestQuery, UserQuery, graphene.ObjectType):
    pass
    
schema = graphene.Schema(query=Query)