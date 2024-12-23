from uuid import UUID
from graphql import GraphQLError

def graphql_error(error_msg: str):
    raise GraphQLError(error_msg)

def internal_server_error(error_msg: str):
    raise GraphQLError(f'Internal Server Error:\n{error_msg}')

def authentication_error(error_msg: str):
    raise GraphQLError(f'Authentication Error:\n{error_msg}')

def authorization_error(error_msg: str):
    raise GraphQLError(f'Authorization Error:\n{error_msg}')

def not_found_error(error_msg:str):
    raise GraphQLError(f'Resource Not Found Error:\n{error_msg}')

def user_not_found(username: str):
    not_found_error(f'User "{username}" does not exist')

def community_not_found(name: str):
    not_found_error(f'Community "{name}" does not exist')
    
def post_not_found(id: UUID):
    not_found_error(f'Post "{id}" does not exist')
    
def comment_not_found(id: UUID):
    not_found_error(f'Comment "{id}" does not exist')