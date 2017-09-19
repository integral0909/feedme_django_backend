from django.conf import settings
from common.utils import traverse_and_compare


class DeeplinkException(Exception):
    pass


class DeeplinkMiddleware(object):
    def __init__(self, get_response):
        """Configuration and initialization at server start."""
        self.get_response = get_response
        self._load_settings()

    def _load_settings(self):
        """Configure DeeplinkMiddleware for use by loading settings."""
        self.config = {
            'user_agents': settings.DEEPLINKER['USER_AGENTS'],
        }

    def __call__(self, request):
        """
        Executed for each request.

        `temp` is emptied and re-populated for each request.
        `temp` stores `useragent_is_target` and `match`.
        """
        # Before the view (and later middleware) are called.
        self.temp = {}
        self.set_deeplink_attrs(request)
        response = self.get_response(request)
        # After the view is called.
        return response

    def set_deeplink_attrs(self, request):
        """Set deeplink attributes on request object, such as flag and deeplink path."""
        request.deeplink = {'useragent_is_target': False}
        request.deeplink['useragent_is_target'] = self._check_user_agent(request)


    def _check_user_agent(self, request):
        """Traverse user_agents tree and check request."""
        return traverse_and_compare(
            tree=self.config['user_agents'], comparison='contains',
            obj=request.user_agent, leaf_type=(list, tuple, set)
        )


def context_processor(request):
    """Take deeplink variables from request and add them to context."""
    try:
        context = {'deeplink': {
            'useragent_is_target': request.deeplink.get('useragent_is_target', False),
        }}
    except AttributeError as e:
        return {}
    print(context)
    return context
