from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
import jose.exceptions
from jose import jwt
import requests


class FirebaseJWTBackend(authentication.BaseAuthentication):
    target_audience = settings.FIREBASE_JWT_BACKEND['target_audience']
    cert_url = settings.FIREBASE_JWT_BACKEND['cert_url']

    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
        print(token)
        if len(token) < 2:
            return None
        #  Need to save tokens and look them up from Database before re-decoding
        res = requests.get(self.cert_url)
        certs = res.json()  # This call to get the cert needs to be cached
        try:
            userData = jwt.decode(token, certs,
                                  algorithms='RS256', audience=self.target_audience)
            auth = {'claims': userData}
        except jose.exceptions.ExpiredSignatureError:
            print('ExpiredSignatureError: Signature has expired')
            raise exceptions.AuthenticationFailed('Invalid token')
        try:
            user = User.objects.get(profile__firebase_id=userData['sub'])
            return (user, auth)
        except User.DoesNotExist:
            firebase = userData.get('firebase', {})
            email = userData.get('email', '')[:254]
            username = firebase['identities'].get('uid', email)[:150]
            if isinstance(username, list, tuple, set):
                username = username[0][:150]
            params = {
                'email': email, 'username': username,
                'first_name': firebase['identities'].get('firstname', '')[:30],
                'last_name': firebase['identities'].get('lastname', '')[:30],
            }
            user = User(**params)
            user.save()
            profile = Profile(provider=firebase['sign_in_provider'],
                              firebase_id=userData['sub'], user=user)
            if firebase['sign_in_provider'] == 'facebook.com':
                profile.fb_id = username
                profile.photo_url = firebase['identities'].get('photoURL', '')
            profile.save()
            return (user, auth)
