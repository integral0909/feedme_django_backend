from django.views import View
from django_sqs_jobs.jobs import Job
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseBadRequest
import json
# Need to define a single view that will receive messages.
# It's up to consumer to route requests
# Find consumer's jobs via
# for job in Job.__subclasses__():

class JobMessageException(Exception):
    pass


class InvalidContentType(JobMessageException):
    pass


class EmptyRequestBody(JobMessageException):
    pass


class PostBodyParseError(JobMessageException):
    pass


@method_decorator(csrf_exempt, name='dispatch')
class JobMessageView(View):
    allowed_methods = ['post', 'options']

    def post(self, request):
        try:
            self.validate_post_body(request)
            self.data = self.process_post_body(request)
        except JobMessageException as e:
            return HttpResponseBadRequest(str(e))
        else:
            return self.execute_job(data)

    def execute_job(self):
        """Execute the Job specified in the request"""
        job = [j for j in Job.__subclasses__()
               if j.__class__.__name__ == self.data['JOB']][0]()
        job(*self.data['ARGS'], **self.data['KWARGS'])
        return HttpResponse('OK')


    def validate_post_body(self, request, content_type='application/json'):
        """
        Verifies that the request has a valid body and content type, default JSON.
        """
        if len(request.body) == 0:
            raise InvalidContentType('Empty request body')
        if content_type not in request.content_type:
            raise EmptyRequestBody('Invalid Content-Type: %s only' % content_type)
        return True

    def process_post_body(self, request):
        """
        Transforms JSON post body into dict and returns it.

        Returns a 400 Response if invalid.
        """
        try:
            return json.loads(request.body)
        except Exception as e:
            json_data = {'error': '{0}'.format(str(e))}
            raise PostBodyParseError(json.dumps(json_data))
