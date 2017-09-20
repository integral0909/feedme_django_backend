from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from common.utils import divide_or_zero
from main.models import DishQuery, Like, RecipeLike


class UsersViewset(APIView):
    permission_classes = (IsAdminUser, )

    def get(self, request, format=None):
        return Response({'users': User.objects.count()})


class EngagementViewset(APIView):
    """Engagement stats."""
    permission_classes = (IsAdminUser, )

    def get(self, request, format=None):
        qs = User.objects.annotate(likes_count=Count('likes')).filter(likes_count__gte=1)
        qsr = User.objects.annotate(likes_count=Count('recipe_likes'))\
                          .filter(likes_count__gte=1)
        dish_swipers_count = qs.count()
        recipe_swipers_count = qsr.count()
        non_swipers_count = User.objects.annotate(rlikes_cnt=Count('likes',
                                                                   distinct=True),
                                                  likes_cnt=Count('recipe_likes',
                                                                  distinct=True))\
                                        .filter(rlikes_cnt=0, likes_cnt=0).count()
        data = {
            'swipes': {
                'count': [
                    qs.filter(likes_count__gte=100).count(),
                    qs.filter(likes_count__gte=50, likes_count__lte=99).count(),
                    qs.filter(likes_count__gte=20, likes_count__lte=49).count(),
                    qs.filter(likes_count__gte=1, likes_count__lte=19).count()
                ]
            },
            'recipe_swipes': {
                'count': [
                    qsr.filter(likes_count__gte=100).count(),
                    qsr.filter(likes_count__gte=50, likes_count__lte=99).count(),
                    qsr.filter(likes_count__gte=20, likes_count__lte=49).count(),
                    qsr.filter(likes_count__gte=1, likes_count__lte=19).count()
                ]
            },
            'non_swipers': non_swipers_count
        }
        data['swipes']['percent'] = [
            '{:.2f}'.format(divide_or_zero(n, dish_swipers_count) * 100)
            for n in data['swipes']['count']]
        data['recipe_swipes']['percent'] = [
            '{:.2f}'.format(divide_or_zero(n, recipe_swipers_count) * 100)
            for n in data['recipe_swipes']['count']]
        return Response(data)


class RecentEngagementViewset(APIView):
    """Last 24 hrs engagement stats."""
    permission_classes = (IsAdminUser, )

    def get(self, request, format=None):
        day_ago = timezone.now() - timedelta(hours=24)
        qs = User.objects.filter(date_joined__gte=day_ago)
        recent_users = User.objects.filter(
            Q(dish_queries__created__gte=day_ago) | Q(recipe_queries__created__gte=day_ago)
        ).distinct().count()
        new_users = qs.count()
        new_queries = DishQuery.objects.filter(created__gte=day_ago).count()
        new_swipes = Like.objects.filter(created__gte=day_ago).count()
        new_rswipes = RecipeLike.objects.filter(created__gte=day_ago).count()
        qs = qs.annotate(likes_count=Count('likes'))
        qsr = qs.annotate(likes_count=Count('recipe_likes'))
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
            'recipe_swipes': {
                'count': [
                    qsr.filter(likes_count__gte=100).count(),
                    qsr.filter(likes_count__gte=50, likes_count__lte=99).count(),
                    qsr.filter(likes_count__gte=20, likes_count__lte=49).count(),
                    qsr.filter(likes_count__gte=1, likes_count__lte=19).count(),
                    qsr.filter(likes_count=0).count()
                ]
            },
            'new_signups': new_users,
            'recent_users': recent_users,
            'new_queries': new_queries,
            'new_swipes': new_swipes,
            'new_rswipes': new_rswipes,
        }
        data['swipes']['percent'] = ['{:.2f}'.format(divide_or_zero(n, new_users) * 100)
                                     for n in data['swipes']['count']]
        data['recipe_swipes']['percent'] = [
            '{:.2f}'.format(divide_or_zero(n, new_users) * 100)
            for n in data['recipe_swipes']['count']
        ]
        return Response(data)
