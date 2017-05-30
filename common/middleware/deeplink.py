from django.conf import settings
from django.utils.module_loading import import_string
from django.urls import resolve, Resolver404
from common.utils import traverse_and_compare


class DeeplinkException(Exception):
    pass


class DeeplinkNotFound(DeeplinkException):
    pass


class DeeplinkMiddleware(object):
    def __init__(self, get_response):
        """Configuration and initialization at server start."""
        self.get_response = get_response
        self._load_settings()

    def _load_settings(self):
        """Configure DeeplinkMiddleware for use by loading settings."""
        urlpatterns = import_string(settings.DEEPLINKER['URL_MODULE'] + '.urlpatterns')
        self.config = {
            'user_agents': settings.DEEPLINKER['USER_AGENTS'],
            'urlpatterns': urlpatterns,
            'protocol': settings.DEEPLINKER['PROTOCOL'],
            'base': settings.DEEPLINKER.get('BASE', '')
        }

    def __call__(self, request):
        """
        Executed for each request.

        `temp` is emptied and re-populated for each request.
        `temp` stores `useragent_is_target` and `match`.
        """
        # Before the view (and later middleware) are called.
        self.temp = {}
        try:
            self.set_deeplink_attrs(request)
        except DeeplinkNotFound as e:
            if settings.DEBUG:
                print(e)
        finally:
            response = self.get_response(request)
        # After the view is called.
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """If view_func has deeplink_only then render a deeplink template."""
        if not self.temp.get('match', False) and hasattr(view_func, 'deeplink_path'):
            self._resolve_deeplink_path(view_func.deeplink_path)
        try:
            if view_func.deeplink_only and self.temp.get('match', False):
                view_func = self.temp['match'].func
                return view_func(request, *view_args, **view_kwargs)
            elif view_func.deeplink_only:
                raise DeeplinkNotFound(
                    "No matching deeplink url found for deeplink_only view: "
                    + view_func.__name__)
        except AttributeError as e:
            if 'deeplink_only' in str(e):
                pass
            else:
                print(e)

    def set_deeplink_attrs(self, request):
        """Set deeplink attributes on request object, such as flag and deeplink path."""
        request.deeplink = {'has_deeplink': False, 'useragent_is_target': False,
                            'all_conditions_met': False}
        request.deeplink['has_deeplink'] = self._resolve_deeplink_path(request.path)
        request.deeplink['useragent_is_target'] = self._check_user_agent(request)

        if (request.deeplink['has_deeplink']
           and request.deeplink['useragent_is_target']):
            request.deeplink['all_conditions_met'] = True

        if request.deeplink['has_deeplink']:
            dl_path = '%s%s%s' % (self.config['protocol'], self.config['base'],
                                  request.path.lstrip('/'))
            request.deeplink['path'] = dl_path

    def _resolve_deeplink_path(self, path):
        """
        Checks deeplink urlpatterns for matching path

        https://docs.djangoproject.com/en/1.10/ref/urlresolvers/#django.urls.ResolverMatch
        """
        try:
            self.temp['match'] = resolve(path, settings.DEEPLINKER['URL_MODULE'])
        except Resolver404:
            raise DeeplinkNotFound("Could not resolve deeplink for " + path)
        return True

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
            'all_conditions_met': request.deeplink['all_conditions_met'],
            'path': request.deeplink.get('path', None),
            'useragent_is_target': request.deeplink.get('useragent_is_target', False),
            'has_deeplink': request.deeplink['has_deeplink']
        }}
    except AttributeError as e:
        return {}
    return context
