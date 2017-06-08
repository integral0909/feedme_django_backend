from datetime import datetime, timedelta, timezone
from django.contrib.auth.models import User
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework import viewsets, generics, pagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from common.utils import divide_or_zero
from main.models import DishQuery, Like


class UsersViewset(APIView):
    permission_classes = (IsAdminUser, )

    def get(self, request, format=None):
        return Response({'users': User.objects.count()})


class EngagementViewset(APIView):
    """Engagement stats."""
    permission_classes = (IsAdminUser, )

    def get(self, request, format=None):
        qs = User.objects.annotate(likes_count=Count('likes'))
        users_count = User.objects.count()
        data = {
            'swipes': {
                'count': [
                    qs.filter(likes_count__gte=100).count(),
                    qs.filter(likes_count__gte=50, likes_count__lte=99).count(),
                    qs.filter(likes_count__gte=20, likes_count__lte=49).count(),
                    qs.filter(likes_count__gte=1, likes_count__lte=19).count(),
                    qs.filter(likes_count=0).count()
                ]
            }
        }
        data['swipes']['percent'] = ['{:.2f}'.format(divide_or_zero(n, users_count) * 100)
                                     for n in data['swipes']['count']]
        return Response(data)


class RecentEngagementViewset(APIView):
    """Last 24 hrs engagement stats."""
    permission_classes = (IsAdminUser, )

    def get(self, request, format=None):
        day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        qs = User.objects.filter(last_login__gte=day_ago)
        new_users = qs.count()
        new_queries = DishQuery.objects.filter(created__gte=day_ago).count()
        new_swipes = Like.objects.filter(created__gte=day_ago).count()
        qs = qs.annotate(likes_count=Count('likes'))
        data = {
            'swipes': {
                'count': [
                    qs.filter(likes_count__gte=100).count(),
                    qs.filter(likes_count__gte=50, likes_count__lte=99).count(),
                    qs.filter(likes_count__gte=20, likes_count__lte=49).count(),
                    qs.filter(likes_count__gte=1, likes_count__lte=19).count(),
                    qs.filter(likes_count=0).count()
                ]
            },
            'new_users': new_users,
            'new_queries': new_queries,
            'new_swipes': new_swipes
        }
        data['swipes']['percent'] = ['{:.2f}'.format(divide_or_zero(n, new_users) * 100)
                                     for n in data['swipes']['count']]
        return Response(data)
