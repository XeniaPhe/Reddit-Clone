from django.db.models import Q
from core.models import User
from core.custom_errors import graphql_error, user_not_found, user_deleted

def get_user(username: str) -> User | None:
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        user_not_found(username)
        
def get_user_with_email(email: str) -> User | None:
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        user_not_found(email)
        
def fetch_user(username_or_email: str, error_msg=None):
    try:
        return User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
    except User.DoesNotExist:
        if error_msg:
            raise graphql_error('Resource Not Found', error_msg)
        else:
            user_not_found(username_or_email)

def get_unremoved_user(username: str):
    user = get_user(username)
    if not user.is_active:
        user_deleted(username)
    
    return user

def get_unremoved_user_with_email(email: str):
    user = get_user_with_email(email)
    if not user.is_active:
        user_deleted(email)
    
    return user

def fetch_unremoved_user(username_or_email: str, error_msg=None):
    user = fetch_user(username_or_email, error_msg)
    if not user.is_active:
        user_deleted(username_or_email)
    
    return user

def assert_user_exists(username: str):
    get_user(username)
    
def assert_user_exists_with_email(email: str):
    get_user_with_email(email)

def assert_user(username: str):
    get_unremoved_user(username)
    
def assert_user_with_email(email: str):
    get_unremoved_user_with_email(email)