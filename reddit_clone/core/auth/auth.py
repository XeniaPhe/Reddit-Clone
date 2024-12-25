import jwt
from django.conf import settings
from datetime import datetime, timedelta
from functools import wraps

from core.models import User, Membership
from core.custom_errors import internal_server_error, authentication_error, authorization_error
from core.auth.roles import GUEST, MEMBER, ADMIN, ROLE_CHOICES, permission_granted
from core.services import get_user, assert_community_exists

def create_jwt_token(user: User):
    payload = {
        'username': user.username,
        'is_admin': user.is_superuser,
        'exp': datetime.now() + timedelta(hours=1)
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def require_jwt(community_param, required_role=MEMBER):
    def decorator(func):
        @wraps(func)
        def wrapper(root, info, *args, **kwargs):
            request = info.context.request
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                authentication_error('Authorization header missing')
            
            if not auth_header.startswith('JWT '):
                authentication_error('Authorization header must be a JWT token')
            
            jwt_token = auth_header[len('JWT '):]
            
            try:
                payload = jwt.decode(jwt_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                username, is_admin = payload['username'], payload['is_admin']
                community_name = kwargs.get(community_param, None)
                
                if community_name is None:
                    internal_server_error(f'Parameter {community_param} not found in kwargs')
                
                assert_community_exists(community_name)
                    
                membership = Membership.objects.filter(user_id=username, community_id=community_name).first()
                user_role = membership.role if membership else ADMIN if is_admin else GUEST
                
                if not permission_granted(required_role, user_role):
                    authorization_error(f'Authorization failed:\n    User "{username}" does not have the required role'+
                                       +f'"{ROLE_CHOICES[required_role]}". Current role: "{ROLE_CHOICES[user_role]}"')
                    
                request.user = get_user(username)
                
            except jwt.ExpiredSignatureError:
                authentication_error('The JWT token has expired')
            except jwt.exceptions.InvalidTokenError:
                authentication_error('Invalid JWT token')
            
            return func(root, info, *args, **kwargs)
        return wrapper
    return decorator