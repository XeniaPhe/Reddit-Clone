from graphql import GraphQLError

def internal_server_error(error_msg: str):
    raise GraphQLError(f'Internal Server Error:\n{error_msg}')

def authentication_error(error_msg: str):
    raise GraphQLError(f'Authentication Error:\n{error_msg}')

def authorization_error(error_msg: str):
    raise GraphQLError(f'Authorization Error:\n{error_msg}')

def not_found(error_msg:str):
    raise GraphQLError(f'Not Found:\n{error_msg}')