import jwt
from django.conf import settings
from datetime import datetime, timedelta
from functools import wraps

from core.models import User, Membership, Community
from core.custom_errors import internal_server_error, authentication_error, authorization_error, not_found
from core.auth.roles import *

def create_jwt_token(user: User):
    payload = {
        'username': user.username,
        'is_admin': user.is_superuser,
        'exp': datetime.now() + timedelta(hours=1)
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def require_jwt(community_param, required_role=Membership.MEMBER):
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
                
                if not Community.objects.filter(name=community_name).exists():
                    not_found(f'Community "{community_name}" does not exist')
                    
                membership = Membership.objects.filter(user_id=username, community_id=community_name).first()
                user_role = membership.role if membership else ADMIN if is_admin else GUEST
                
                if not permission_granted(required_role, user_role):
                    authorization_error(f'Authorization failed: User "{username}" does not have the required role'+
                                       +f'"{required_role}". Current role: "{ROLE_CHOICES_REVERSE[user_role]}"')
                    
                user = User.objects.get(username=username)
                request.user = user
                
            except jwt.ExpiredSignatureError:
                authentication_error('The jwt token has expired')
            except jwt.exceptions.InvalidTokenError:
                authentication_error('Invalid jwt token')
            except User.DoesNotExist:
                authentication_error(f'User "{username}" does not exist')
            
            return func(root, info, *args, **kwargs)
        return wrapper
    return decorator