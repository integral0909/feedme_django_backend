from django_sqs_jobs import WORKER_QUEUE
from .jobs import OnboardingComposite, OnboardUserFacebook, OnboardUserMailchimp


def enqueue_onboarding(sender, instance, created, **kwargs):
    if created:
        WORKER_QUEUE.append(OnboardingComposite(OnboardUserMailchimp(instance.user.id),
                                                OnboardUserFacebook(instance.user.id)))