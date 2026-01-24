from django import template

register = template.Library()


@register.filter
def has_role(user, role_name):
    """
    Template filter to check if a user has a specific role.
    Usage: {% if request.user|has_role:"User Manager" %}
    """
    if not user.is_authenticated:
        return False
    return user.has_role(role_name)
