from django_sqs_jobs import jobs
from django.db import models
import boto3


class PrepopulateDraft(jobs.Job):
    s3 = boto3.resource('s3')

    def args_parser(self):
        self.ARGS = [a.id if issubclass(a.__class__, models.Model) else a
                     for a in self.ARGS]
        return self.ARGS

    def exec(self, instance_id, class_name, **kwargs):
        import data_entry.models
        draft_class = getattr(data_entry.models, class_name)
        draft = draft_class.objects.get(pk=instance_id)
        draft.prepopulate_with_raw()
        draft.prepopulate_image(self.s3)
