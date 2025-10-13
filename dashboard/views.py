from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from courses.models import Course, Enrollment
from chat.models import ChatRoom


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Статистики за корисникот
        if user.user_type == 'student':
            context['enrollments'] = Enrollment.objects.filter(
                student=user,
                is_active=True
            ).select_related('course')[:6]
            context['total_enrollments'] = Enrollment.objects.filter(
                student=user,
                is_active=True
            ).count()
            context['completed_courses'] = Enrollment.objects.filter(
                student=user,
                is_completed=True
            ).count()

        elif user.user_type == 'instructor':
            context['my_courses'] = Course.objects.filter(
                instructor=user
            ).order_by('-created_at')[:6]
            context['total_students'] = Enrollment.objects.filter(
                course__instructor=user,
                is_active=True
            ).count()
            context['total_courses'] = Course.objects.filter(
                instructor=user
            ).count()

        # Најнови курсеви
        context['latest_courses'] = Course.objects.filter(
            status='published'
        ).order_by('-created_at')[:6]

        # Активни чет соби
        context['active_chat_rooms'] = ChatRoom.objects.filter(
            participants=user,
            is_active=True
        ).order_by('-created_at')[:5]

        return context


class MyCoursesView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/my_courses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.user_type == 'student':
            context['enrollments'] = Enrollment.objects.filter(
                student=user,
                is_active=True
            ).select_related('course').order_by('-enrolled_at')

        elif user.user_type == 'instructor':
            context['courses'] = Course.objects.filter(
                instructor=user
            ).order_by('-created_at')

        return context
