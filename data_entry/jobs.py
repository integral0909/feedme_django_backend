from django_sqs_jobs import jobs
import boto3


class PrepopulateImage(jobs.Job):
    s3 = boto3.resource('s3')

    def exec(self, *args, **kwargs):
        from data_entry.models import RecipeDraft
        draft = RecipeDraft.objects.get(pk=args[0])
        draft.prepopulate_image(self.s3)
