from uuid import UUID
from graphql import GraphQLError

def graphql_error(title: str, description: str):
    raise GraphQLError(f'{title}:\n    {description}')

def internal_server_error(error_msg: str):
    graphql_error('Internal Server Error', error_msg)

def authentication_error(error_msg: str):
    graphql_error('Authentication Error', error_msg)

def authorization_error(error_msg: str):
    graphql_error('Authorization Error', error_msg)

def bad_request(error_msg: str):
    graphql_error('Bad Request', error_msg)

def not_found(error_msg: str):
    graphql_error('Resource Not Found', error_msg)
    
def filter_error(error_msg: str):
    internal_server_error(f'Filter Error:\n    {error_msg}')
    
def pagination_error(error_msg: str):
    bad_request(f'Pagination Error:\n    {error_msg}')

def user_not_found(username: str):
    not_found(f'User "{username}" does not exist')

def community_not_found(name: str):
    not_found(f'Community "{name}" does not exist')
    
def post_not_found(id: UUID):
    not_found(f'Post "{id}" does not exist')
    
def comment_not_found(id: UUID):
    not_found(f'Comment "{id}" does not exist')