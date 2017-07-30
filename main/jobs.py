from django_sqs_jobs import Job, CompositeJob
from mailchimp3 import MailChimp
import requests
import os

mc = MailChimp(os.environ.get('MAILCHIMP_USERNAME', 'testusername'),
               os.environ.get('MAILCHIMP_KEY', 'testkey'))
fb_api = 'https://graph.facebook.com/v2.10/'
fb_fields = 'id,name,age_range,gender,email'
fb_token = os.environ.get('FB_TOKEN')


class OnboardUser(Job):
    def setup(self, user_id):
        from main.models import Profile
        self.profile = Profile.objects.get(user__id=user_id)

class OnboardUserMailchimp(OnboardUser):
    def exec(self, *args, **kwargs):
        if self.profile.user.email:
            data = {
                'merge_fields': {
                    'FNAME': self.profile.user.first_name, 'LNAME': self.profile.user.last_name
                }, 'email_address': self.profile.user.email, 'status': 'subscribed',
            }
            mc.lists.members.create(list_id='83d8f50620', data=data)


class OnboardUserFacebook(OnboardUser):
    def exec(self, *args, **kwargs):
        if not self.profile.fb_id:
            return
        r = requests.get('{fb_api}{fb_id}?fields={fb_fields}&access_token={fb_token}'.format(
            fb_id=self.profile.fb_id, fb_token=fb_token, fb_api=fb_api, fb_fields=fb_fields
        ))
        data = r.json()
        age_range = data.get('age_range', {})
        self.profile.age_max = age_range.get('max')
        self.profile.age_min = age_range.get('min')
        self.profile.gender = data.get('gender', '')
        self.profile.user.email = data.get('email', '')
        self.profile.save()
        self.profile.user.save()


class OnboardingComposite(CompositeJob):
    pass
