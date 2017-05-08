from django.utils.deprecation import MiddlewareMixin
from django_user_agents.middleware import UserAgentMiddleware


class CustomUserAgentMiddleware(MiddlewareMixin, UserAgentMiddleware):
    pass
