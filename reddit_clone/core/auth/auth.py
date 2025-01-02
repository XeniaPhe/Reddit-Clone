import jwt
from django.conf import settings
from datetime import datetime, timedelta
from functools import wraps

from core.models import User, Membership
from core.custom_errors import internal_server_error, authentication_error, authorization_error
from core.auth.roles import GUEST, MEMBER, ADMIN, ALL_ROLES, permission_granted
from core.services import get_user, assert_community_exists

def create_jwt_token(user: User):
    payload = {
        'username': user.username,
        'is_admin': user.is_superuser,
        'exp': datetime.now() + timedelta(hours=24 * 10),
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

#TODO: add a blacklist to jwt tokens

def require_authentication(require_admin=False):
    def decorator(func):
        @wraps(func)
        def wrapper(root, info, *args, **kwargs):
            print(f"1:{info is None}")
            
            request = info.context.request
            auth_header = request.headers.get('Authorization')

            if not auth_header:
                authentication_error('Authorization header missing')
            if not auth_header.startswith('JWT '):
                authentication_error('Authorization header must be a JWT token')

            jwt_token = auth_header[len('JWT '):]

            try:
                payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                username, is_admin = payload['username'], payload['is_admin']
                
                if require_admin and not is_admin:
                    authorization_error(f'The user "{username}" does not have admin priviliges')
                
                request.user = get_user(username)
                
            except jwt.ExpiredSignatureError:
                authentication_error('The JWT token has expired')
            except jwt.exceptions.InvalidTokenError:
                authentication_error('Invalid JWT token')
                
            return func(root, info, *args, **kwargs)
        return wrapper
    return decorator
            
def require_authorization(community_param, required_role=MEMBER):
    def decorator(func):
        @wraps(func)
        def wrapper(root, info, *args, **kwargs):
            user = info.context.request.user
            if not user:
                internal_server_error('The request does not contain a valid user, '
                                    + 'authentication may have failed or user information is missing')
            
            community_name = kwargs.get(community_param, None)
            if not community_name:
                internal_server_error(f'Parameter {community_param} not found in kwargs')
                
            assert_community_exists(community_name)
            membership = Membership.objects.filter(user_id=user.username, community_id=community_name).first()
            user_role = ADMIN if user.is_superuser else (membership.role if membership else GUEST)
                
            if not permission_granted(required_role, user_role):
                authorization_error(f'User "{user.username}" does not have the required role '
                                    f'"{ALL_ROLES[required_role]}". Current role: "{ALL_ROLES[user_role]}"')
                    
            return func(root, info, *args, **kwargs)
        return wrapper
    return decorator