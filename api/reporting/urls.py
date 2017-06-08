from django.conf.urls import url, include
from api.reporting import views

urlpatterns = [
    url(r'^engagement/', views.EngagementViewset.as_view()),
    url(r'^users/', views.UsersViewset.as_view()),
    url(r'^recent/', views.RecentEngagementViewset.as_view()),
]
