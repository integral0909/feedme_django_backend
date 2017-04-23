class DeeplinkMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if request.user_agent.device.family in ['iPhone', 'iOS-Device']:
            return self.get_deeplink_response(request)

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def get_deeplink_response(request):
        """Return a response for deeplinks"""
        pass
