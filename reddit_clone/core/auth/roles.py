from core.custom_errors import internal_server_error

GUEST, MEMBER, MODERATOR, FOUNDER, ADMIN = 'Gst', 'Mem', 'Mod', 'Fdr', 'Adm'
ROLE_CHOICES = {
    MEMBER: 'Member',
    MODERATOR: 'Moderator',
    FOUNDER: 'Founder',
}

ROLE_CHOICES_REVERSE = {GUEST:GUEST, ADMIN:ADMIN} | {v:k for k, v in ROLE_CHOICES}

#Is permission granted given owned and required roles of the community and the admin status (is_admin field in the User)
def permission_granted(required_role, user_role):
    if required_role == GUEST:
        return True
    if required_role == ADMIN:
        return False
    if user_role == ROLE_CHOICES[FOUNDER]:
        return True
    if required_role == FOUNDER:
        return False
    if user_role == ROLE_CHOICES[MODERATOR]:
        return True
    if required_role == MODERATOR:
        return False
    if user_role == ROLE_CHOICES[MEMBER]:
        return True
    if required_role == MEMBER:
        return False
    
    internal_server_error('Undefined role')