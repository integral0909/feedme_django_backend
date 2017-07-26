from django.test import TestCase, SimpleTestCase, RequestFactory
from django_sqs_jobs import jobs, queues, views, daemons

TEST_JOBS = ['django_sqs_jobs.tests.JobExample',
             'django_sqs_jobs.tests.JobExampleDivision']


class JobExample(jobs.Job):
    def exec(self, val):
        return val * 2


class JobExampleDivision(jobs.Job):
    def exec(self, numerator, denominator):
        return numerator / denominator


class TestLocalQueue(SimpleTestCase):
    def setUp(self):
        self.queue = queues.LocalQueue()

    def tearDown(self):
        self.queue = None

    def test_local_queue(self):
        self.assertEqual(self.queue.name, 'local')
        self.queue.append(JobExample(5))
        for job in self.queue:
            self.assertEqual(job(), 10)

    def test_local_queue_extends(self):
        self.queue.extend([JobExample(2), JobExample(3), JobExample(4)])
        for idx, job in enumerate(self.queue):
            self.assertEqual(job(), (idx+2)*2)

    def test_multiple_jobs(self):
        self.queue.extend([JobExample(2), JobExampleDivision(8, 2), JobExample(4)])
        self.assertEqual(self.queue[0](), 4)
        self.assertEqual(self.queue[1](), 4)
        self.assertEqual(self.queue[2](), 8)

    def test_composite_jobs(self):
        cjob = jobs.CompositeJob(JobExample(3), JobExampleDivision(9, 3),
                                 allowed_jobs=TEST_JOBS)
        self.queue.append(cjob)
        results = self.queue[0]()
        self.assertEqual(results[0], 6)
        self.assertEqual(results[1], 3)

    def test_composite_jobs_encoded_jobs(self):
        cjob = jobs.CompositeJob(JobExample(3), JobExampleDivision(9, 3),
                                 allowed_jobs=TEST_JOBS)
        cjob.args_parser()
        self.queue.append(cjob)
        results = self.queue[0]()
        self.assertEqual(results[0], 6)
        self.assertEqual(results[1], 3)

    def test_composite_jobs_encode_decode(self):
        cjob = jobs.CompositeJob(JobExample(3), JobExampleDivision(9, 3),
                                 allowed_jobs=TEST_JOBS)
        cjob_raw = cjob.encode()
        decoded = jobs.Job.decode(cjob_raw, {'CompositeJob': jobs.CompositeJob})
        results = decoded()
        self.assertEqual(results[0], 6)
        self.assertEqual(results[1], 3)

    def test_composite_jobs_double_encode(self):
        cjob = jobs.CompositeJob(JobExample(3), JobExampleDivision(9, 3),
                                 allowed_jobs=TEST_JOBS)
        cjob.args_parser()
        cjob_raw = cjob.encode()
        decoded = jobs.Job.decode(cjob_raw, {'CompositeJob': jobs.CompositeJob})
        results = decoded()
        self.assertEqual(results[0], 6)
        self.assertEqual(results[1], 3)


class TestJobMessageView(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.jmv = views.JobMessageView.as_view(allowed_jobs=TEST_JOBS)

    def test_view_job_decode(self):
        req = self.factory.post(
            '/',  # Irrelevant for test
            '{"JOB": "JobExample", "ARGS": [3], "KWARGS": {}}',
            content_type='application/json'
        )
        res = self.jmv(req)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content.decode('utf-8'), '6')

    def test_view_job_empty(self):
        req = self.factory.post(
            '/',  # Irrelevant for test
            '',
            content_type='application/json'
        )
        res = self.jmv(req)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'), 'Empty request body')

    def test_view_job_bad_content_type(self):
        req = self.factory.post(
            '/',  # Irrelevant for test
            '{"JOB": "JobExample", "ARGS": [3], "KWARGS": {}}',
            content_type='text/html'
        )
        res = self.jmv(req)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'),
                         'Invalid Content-Type: application/json only')

    def test_view_job_bad_exec(self):
        req = self.factory.post(
            '/',  # Irrelevant for test
            '{"JOB": "JobExample", "ARGS": [], "KWARGS": {}}',
            content_type='application/json'
        )
        res = self.jmv(req)
        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.content.decode('utf-8'),
                         '{"error": "Error during execution of JobExample"}')