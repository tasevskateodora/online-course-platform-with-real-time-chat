from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('my-courses/', views.MyCoursesView.as_view(), name='my_courses'),
]