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
from rest_framework.authentication import SessionAuthentication, BasicAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class ScraperAuthentication(BasicAuthentication):
    pass


class FirebaseAuthException(Exception):
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

    def authenticate(self, request, retry=True):
        client.context.merge({'request': request})
        try:
            token = self._get_auth_token(request)
        except FirebaseAuthTokenMissing:
            print('Auth token missing')
            return None  # Necessary for session based api explorer
        tokenClaims = self.validate_token(token)
        auth = {'claims': tokenClaims}
        try:
            user = self._get_user(tokenClaims['sub'])
            return (user, auth)
        except User.DoesNotExist:
            try:
                user, profile = self._create_user(tokenClaims)
            except IntegrityError:
                # >1 concurrent requests /\ race conditions -> a parallel thread created account: reauth
                return self.authenticate(request, retry=False) if retry else None
            else:
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
        first_name, last_name = self._get_names(tokenClaims)
        params = {
            'email': email, 'username': username,
            'first_name': first_name, 'last_name': last_name,
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
            profile.fb_id = self._get_fb_id(firebase['identities'])
        profile.photo_url = self._get_photo_url(tokenClaims)
        try:
            profile.save()
        except Exception as e:
            print(e)
            user.delete()
            raise ProfileCreationFailed('A profile was not created')
        else:
            return profile

    def _get_names(self, tokenClaims):
        fname = ''
        lname = ''
        try:
            fname = tokenClaims['firebase']['identities']['firstname'][:30]
            lname = tokenClaims['firebase']['identities']['lastname'][:30]
        except KeyError:
            try:
                names = tokenClaims['name'].split(' ')
            except:
                pass
            else:
                fname = names[0]
                lname = names[-1]
        return fname, lname

    def _get_photo_url(self, tokenClaims):
        try:
            return tokenClaims['firebase']['identities']['photoURL']
        except KeyError:
            return tokenClaims.get('picture', '')

    def _get_fb_id(self, identities):
        try:
            return identities.get('uid')[:150]
        except TypeError as e:
            fbid = identities.get('facebook.com', '')[0][:150]
            return fbid
