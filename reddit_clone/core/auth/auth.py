import jwt
from django.conf import settings
from datetime import datetime, timedelta
from functools import wraps

from core.models import User, Membership, Content
from core.services.user_service import get_user
from core.services.community_service import assert_community_exists
from core.services.content_service import get_content, get_related_object
from core.custom_errors import internal_server_error, authentication_error, authorization_error
from core.auth.roles import GUEST, MEMBER, ADMIN, ALL_ROLES, permission_granted

def create_jwt_token(user: User):
    payload = {
        'username': user.username,
        'is_admin': user.is_superuser,
        'exp': datetime.now() + timedelta(hours=24 * 10),
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def optional_authentication(func):
    @wraps(func)
    def wrapper(root, info, *args, **kwargs):
        if info.context.user.is_authenticated:
            return func(root, info, *args, **kwargs)
        
        auth_header = info.context.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('JWT '):
            jwt_token = auth_header[len('JWT '):]
        
            try:
                payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                username = payload['username']
                info.context.user = get_user(username)
            except:
                pass
            
        return func(root, info, *args, **kwargs)
    return wrapper
    
def require_authentication(require_admin=False):
    def decorator(func):
        @wraps(func)
        def wrapper(root, info, *args, **kwargs):
            if info.context.user.is_authenticated:
                return func(root, info, *args, **kwargs)
        
            auth_header = info.context.headers.get('Authorization')

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
                
                info.context.user = get_user(username)
                
            except jwt.ExpiredSignatureError:
                authentication_error('The JWT token has expired')
            except jwt.exceptions.InvalidTokenError:
                authentication_error('Invalid JWT token')
                
            return func(root, info, *args, **kwargs)
        return wrapper
    return decorator
            
def require_community_authorization(community_param, required_role=MEMBER, admin_override=True):
    def decorator(func):
        @wraps(func)
        def wrapper(root, info, *args, **kwargs):
            user = info.context.user
            if not user.is_authenticated:
                internal_server_error('The request does not contain a valid user, '
                                    + 'authentication may have failed or user information is missing')
            
            community_name = kwargs.get(community_param, None)
            if not community_name:
                internal_server_error(f'Parameter {community_param} not found in kwargs')
                
            assert_community_exists(community_name)
            membership = Membership.objects.filter(user_id=user.username, community_id=community_name).first()
            user_role = ADMIN if (admin_override and user.is_superuser) else (membership.role if membership else GUEST)
                
            if not permission_granted(required_role, user_role):
                authorization_error(f'User "{user.username}" does not have the required role '
                                    f'"{ALL_ROLES[required_role]}". Current role: "{ALL_ROLES[user_role]}"')
                    
            return func(root, info, *args, **kwargs)
        return wrapper
    return decorator

def require_content_authorization(user: User, content_id, admin_override=False):
    if not user:
        internal_server_error('The request does not contain a valid user, '
                            + 'authentication may have failed or user information is missing')

    content = get_content(content_id)
    
    if (content.user.username != user.username) and (not admin_override or not user.is_superuser):
        error_msg = f'User {user.username} is not authorized to perform this action. They must be the content owner'
        if admin_override:
            error_msg += f' or have admin priviliges'
        
        authorization_error(error_msg)
        
    return get_related_object(content)