from core.custom_errors import internal_server_error

BANNED, GUEST, MEMBER, MODERATOR, FOUNDER, ADMIN = 'Bnd', 'Gst', 'Mem', 'Mod', 'Fdr', 'Adm'

DB_ROLE_CHOICES = {
    BANNED: 'Banned',
    GUEST: 'Guest',
    MEMBER: 'Member',
    MODERATOR: 'Moderator',
    FOUNDER: 'Founder',
}

ALL_ROLES = DB_ROLE_CHOICES | { ADMIN: 'Admin', }
    
_ROLE_HIERARCHY = [ADMIN, FOUNDER, MODERATOR, MEMBER, GUEST, BANNED]

#Is permission granted given owned and required roles of the community and the admin status (is_admin field in the User)
def permission_granted(required_role, user_role):
    for role in _ROLE_HIERARCHY:
        if user_role == role:
            return True
        elif required_role == role:
            return False
    
    internal_server_error(f'Undefined roles:\n    User role: {user_role}\n    Required role: {required_role}')