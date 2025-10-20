# courses/urls.py

from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Листа и пребарување
    path('', views.CourseListView.as_view(), name='list'),
    path('category/<int:category_id>/', views.CourseListView.as_view(), name='by_category'),

    # Инструктор функции - МОРА да бидат пред <slug:slug>/
    path('create/', views.CourseCreateView.as_view(), name='create'),
    path('my-courses/', views.InstructorCoursesView.as_view(), name='my_courses'),

    # Детали и запишување
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='detail'),
    path('<slug:slug>/enroll/', views.EnrollCourseView.as_view(), name='enroll'),
    path('<slug:slug>/lesson/<int:lesson_id>/', views.LessonDetailView.as_view(), name='lesson_detail'),

    # Управување со курс
    path('<slug:slug>/edit/', views.CourseUpdateView.as_view(), name='edit'),
    path('<slug:slug>/manage/', views.CourseManageView.as_view(), name='manage'),
    path('<slug:slug>/lessons/add/', views.LessonCreateView.as_view(), name='add_lesson'),
    path('<slug:slug>/lessons/<int:lesson_id>/edit/', views.LessonUpdateView.as_view(), name='edit_lesson'),
    path('<slug:slug>/delete/', views.CourseDeleteView.as_view(), name='delete'),
]