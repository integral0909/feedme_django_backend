from raven.contrib.django.raven_compat.models import client
from django.contrib.auth.models import User
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


class FirebaseJWTBackend(authentication.BaseAuthentication):
    target_audience = settings.FIREBASE_JWT_BACKEND['target_audience']
    cert_url = settings.FIREBASE_JWT_BACKEND['cert_url']

    def _get_auth_token(self, request):
        header = request.META.get('HTTP_AUTHORIZATION', '')
        header_split = header.split(' ')
        if header == '':
            return None
        if len(header_split) != 2:
            return None
        if header_split[0] != 'Bearer':
            return None
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

    def authenticate(self, request):
        client.context.merge({'request': request})
        token = self._get_auth_token(request)
        if token is None:
            return None
            # raise FirebaseAuthTokenMissing('JWT token not supplied')
        #  Need to save tokens and look them up from Database before re-decoding
        tokenClaims = self.validate_token(token)
        auth = {'claims': tokenClaims}
        try:
            user = User.objects.get(profile__firebase_id=tokenClaims['sub'])
            return (user, auth)
        except User.DoesNotExist:
            user, profile = self._create_user(tokenClaims)   
            return (user, auth)

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
        user.save()
        profile = self._create_profile(firebase, user, tokenClaims)
        return user, profile

    def _create_pofile(self, firebase, user, tokenClaims):
        profile = Profile(provider=firebase['sign_in_provider'],
                          firebase_id=tokenClaims['sub'], user=user)
        if firebase['sign_in_provider'] == 'facebook.com':
            profile.fb_id = firebase['identities'].get('uid')[:150]
            profile.photo_url = firebase['identities'].get('photoURL', '')
        profile.save()
        return profile
