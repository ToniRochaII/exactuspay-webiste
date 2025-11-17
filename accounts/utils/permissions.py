from accounts.models import PermissionMatrix

def has_permission(user, domain, action):
    if not user.is_authenticated:
        return False
    if getattr(user, "role", "").upper() == "ADMIN":
        return True
    role = getattr(user, "role", "").upper()
    return PermissionMatrix.objects.filter(
        role=role,
        domain__in=["ALL", domain],
        action__in=["ALL", action],
        allowed=True
    ).exists()