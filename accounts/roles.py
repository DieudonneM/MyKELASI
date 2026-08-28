INTERNAL_ROLE_NAMES = (
    "SUPPORT",
    "VERIFICATION",
    "FINANCE",
    "MODERATION",
    "ADMIN",
    "SUPER_ADMIN",
)


def has_internal_role(user, *roles):
    return bool(
        user.is_authenticated
        and user.is_active
        and user.status == "ACTIVE"
        and (user.is_superuser or user.groups.filter(name__in=roles).exists())
    )
