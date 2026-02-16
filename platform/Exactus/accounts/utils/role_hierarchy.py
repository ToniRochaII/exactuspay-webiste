# accounts/utils/role_hierarchy.py

ROLE_ORDER = [
    "EMPLOYEE",
    "SPECIALIST",
    "MANAGER",
    "DIRECTOR",
    "OPERATION",
    "IMPLEMENTATION",
    "BILLING",
    "COMPLIANCE",
    "FINANCE",
    "ADMIN",
    "EXEC",
]

def promote_role(current_role):
    """Return the next higher role, or same role if already at top."""
    if current_role not in ROLE_ORDER:
        return current_role
    index = ROLE_ORDER.index(current_role)
    if index < len(ROLE_ORDER) - 1:
        return ROLE_ORDER[index + 1]
    return current_role  # already at top

def demote_role(current_role):
    """Return the next lower role, or same role if already at bottom."""
    if current_role not in ROLE_ORDER:
        return current_role
    index = ROLE_ORDER.index(current_role)
    if index > 0:
        return ROLE_ORDER[index - 1]
    return current_role  # already lowest
