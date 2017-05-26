from raven.contrib.django.raven_compat.models import client
from django.contrib.auth.models import User
from django.db import IntegrityError
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
import jose.exceptions
from jose import jwt
import requests
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from main.models import Profile


class FirebaseAuthException(exceptions.AuthenticationFailed):
    pass


class FirebaseAuthTokenMissing(FirebaseAuthException):
    pass


class ProfileCreationFailed(exceptions.AuthenticationFailed):
    pass


class UserCreationFailed(exceptions.AuthenticationFailed):
    pass


class FirebaseJWTBackend(authentication.BaseAuthentication):
    target_audience = settings.FIREBASE_JWT_BACKEND['target_audience']
    cert_url = settings.FIREBASE_JWT_BACKEND['cert_url']

    def _get_auth_token(self, request):
        header = request.META.get('HTTP_AUTHORIZATION', '')
        header_split = header.split(' ')
        if header == '':
            raise FirebaseAuthTokenMissing('JWT token not supplied')
        if len(header_split) != 2:
            raise FirebaseAuthTokenMissing('JWT token not supplied')
        if header_split[0] != 'Bearer':
            raise FirebaseAuthTokenMissing('JWT token not supplied')
        return header_split[1]

    def validate_token(self, token):
        sess = CacheControl(requests.Session(),
                            cache=FileCache('%s.web_cache' % settings.TMP_PATH))
        res = sess.get(self.cert_url)
        certs = res.json()
        try:
            tokenClaims = jwt.decode(token, certs, algorithms='RS256',
                                     audience=self.target_audience)
            return tokenClaims
        except jose.exceptions.ExpiredSignatureError:
            print('ExpiredSignatureError: Signature has expired')
            raise exceptions.AuthenticationFailed('Invalid token')

    def authenticate(self, request, depth=0):
        client.context.merge({'request': request})
        token = self._get_auth_token(request)
        tokenClaims = self.validate_token(token)
        auth = {'claims': tokenClaims}
        try:
            user = self._get_user(tokenClaims['sub'])
            return (user, auth)
        except User.DoesNotExist:
            user, profile = self._create_user(tokenClaims)   
            return (user, auth)

    def _get_user(self, sub):
        try:
            user = User.objects.get(profile__firebase_id=sub)
        except User.DoesNotExist:
            user = User.objects.get(username=sub)
        return user


    def _create_user(self, tokenClaims):
        firebase = tokenClaims.get('firebase', {})
        email = tokenClaims.get('email', '')[:254]
        username = tokenClaims['sub']  # Data integrity 
        params = {
            'email': email, 'username': username,
            'first_name': firebase['identities'].get('firstname', '')[:30],
            'last_name': firebase['identities'].get('lastname', '')[:30],
        }
        user = User(**params)
        if user.save() is False:
            raise UserCreationFailed('A user was not created')
        profile = self._create_profile(firebase, user, tokenClaims)
        return user, profile

    def _create_profile(self, firebase, user, tokenClaims):
        profile = Profile(provider=firebase['sign_in_provider'],
                          firebase_id=tokenClaims['sub'], user=user)
        if firebase['sign_in_provider'] == 'facebook.com':
            profile.fb_id = firebase['identities'].get('uid')[:150]
            profile.photo_url = firebase['identities'].get('photoURL', '')
        if profile.save() is False:
            user.delete()
            raise ProfileCreationFailed('A profile was not created')
        return profile

