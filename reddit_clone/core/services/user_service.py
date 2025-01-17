from django.db.models import F, Q
from core.models import User, Community
from core.custom_errors import graphql_error, user_not_found, user_deleted
from core.auth.roles import GUEST, MEMBER, MODERATOR
from core.transact import transact
from core.utils.manager_utils import preselect

def get_user(username: str, select_related: list[str]=None, prefetch_related: list[str]=None):
    try:
        return preselect(User, select_related, prefetch_related).get(username=username)
    except User.DoesNotExist:
        user_not_found(username)
        
def get_user_with_email(email: str, select_related: list[str]=None, prefetch_related: list[str]=None):
    try:
        return preselect(User, select_related, prefetch_related).get(email=email)
    except User.DoesNotExist:
        user_not_found(email)
        
def fetch_user(username_or_email: str, error_msg=None, select_related: list[str]=None, prefetch_related: list[str]=None):
    try:
        return preselect(User, select_related, prefetch_related).get(Q(username=username_or_email) | Q(email=username_or_email))
    except User.DoesNotExist:
        if error_msg:
            raise graphql_error('Resource Not Found', error_msg)
        else:
            user_not_found(username_or_email)

def get_unremoved_user(username: str, select_related: list[str]=None, prefetch_related: list[str]=None):
    user = get_user(username, select_related, prefetch_related)
    if not user.is_active:
        user_deleted(username)
    
    return user

def get_unremoved_user_with_email(email: str, select_related: list[str]=None, prefetch_related: list[str]=None):
    user = get_user_with_email(email, select_related, prefetch_related)
    if not user.is_active:
        user_deleted(email)
    
    return user

def fetch_unremoved_user(username_or_email: str, error_msg=None, select_related: list[str]=None, prefetch_related: list[str]=None):
    user = fetch_user(username_or_email, error_msg, select_related, prefetch_related)
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
    
def delete_user(user: (str | User)):
    if isinstance(user, str):
        user = get_unremoved_user(user, prefetch_related=['memberships'])
    
    transact(transaction, 'An error occured while deleting the user', user)
    
    def transaction(user: User):
        user.is_active = False
        user.is_staff = False
        user.is_superuser = False
        user.save()
        
        memberships = (user.memberships
                       .select_related('community')
                       .filter(role__in=(MEMBER, MODERATOR))) #Founders remain founders of their communities even when deleted
        
        communities = memberships.values_list('community__name', flat=True)
        Community.objects.filter(name__in=communities).update(number_of_members = F('number_of_members') - 1)
        memberships.update(role = GUEST)