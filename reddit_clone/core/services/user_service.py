from django.db.models import Q
from core.models import User
from core.custom_errors import user_not_found, not_found

def fetch_user(username_or_email: str, error_msg=None):
    try:
        return User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
    except User.DoesNotExist:
        if error_msg:
            raise ValueError(error_msg)
        else:
            not_found(f'User with a username or email of {username_or_email} not found')
    
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

def assert_user_exists(username: str):
    get_user(username)
    
def asser_user_exists_with_email(email: str):
    get_user_with_email(email)