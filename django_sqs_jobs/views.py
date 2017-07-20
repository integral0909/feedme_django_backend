from django.views import View
from django_sqs_jobs.jobs import Job
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseBadRequest

# Need to define a single view that will receive messages.
# It's up to consumer to route requests
# Find consumer's jobs via
# for job in Job.__subclasses__():


@method_decorator(csrf_exempt, name='dispatch')
class SQSMessageView(View):
    allowed_methods = ['post', 'options']

    def post(self, request):
        response = self.validate_post_body(request)
        if isinstance(response, HttpResponse):  # This pattern sucks. Use exceptions instead.
            return response

        data = self.process_post_body(request)
        if isinstance(data, HttpResponse):
            return data

        return self.execute_job(data)

    def execute_job(self, data):
        job = [j for j in Job.__subclasses__() if j.__class__.__name__ == data['JOB']][0]
        job(*data['ARGS'], **data['KWARGS'])


    def validate_post_body(self, request, content_type='application/json'):
        """
        Verifies that the request has a valid body and content type, default JSON.
        """
        if len(request.body) == 0:
            return HttpResponseBadRequest('Empty request body')
        if content_type not in request.content_type:
            return HttpResponseBadRequest('Invalid Content-Type: %s only' % content_type)
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
            return HttpResponseBadRequest(json.dumps(json_data), content_type="application/json")
