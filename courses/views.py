# courses/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, Http404
from django.utils import timezone
from .models import Course, Category, Lesson, Enrollment, LessonProgress
from .forms import CourseForm, LessonForm, CourseSearchForm
from chat.models import ChatRoom
from django.views.generic import DeleteView

class CourseListView(ListView):
    model = Course
    template_name = 'courses/list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        queryset = Course.objects.filter(status='published').select_related(
            'instructor', 'category'
        ).annotate(
            enrolled_count=Count('enrollments', filter=Q(enrollments__is_active=True))
        )

        # Филтрирање по категорија
        category_id = self.kwargs.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Пребарување
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(instructor__first_name__icontains=search_query) |
                Q(instructor__last_name__icontains=search_query)
            )

        # Филтрирање по тежина
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Филтрирање по цена
        price_filter = self.request.GET.get('price')
        if price_filter == 'free':
            queryset = queryset.filter(price=0)
        elif price_filter == 'paid':
            queryset = queryset.filter(price__gt=0)

        # Сортирање
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['-created_at', 'title', '-enrolled_count', 'price']:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_form'] = CourseSearchForm(self.request.GET)
        context['current_category'] = self.kwargs.get('category_id')
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/detail.html'
    context_object_name = 'course'

    def get_object(self):
        return get_object_or_404(
            Course.objects.select_related('instructor', 'category'),
            slug=self.kwargs['slug'],
            status='published'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user

        # Провери дали корисникот е запишан
        context['is_enrolled'] = False
        context['enrollment'] = None
        if user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(student=user, course=course, is_active=True)
                context['is_enrolled'] = True
                context['enrollment'] = enrollment
            except Enrollment.DoesNotExist:
                pass

        # Лекции
        context['lessons'] = course.lessons.all().order_by('order')

        # Статистики
        context['total_students'] = course.get_enrolled_count()
        context['completion_rate'] = course.get_completion_rate()

        # Слични курсеви
        context['similar_courses'] = Course.objects.filter(
            category=course.category,
            status='published'
        ).exclude(id=course.id)[:4]

        return context


class EnrollCourseView(LoginRequiredMixin, DetailView):
    model = Course

    def post(self, request, *args, **kwargs):
        course = self.get_object()
        user = request.user

        # Провери дали корисникот веќе е запишан
        enrollment, created = Enrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={'is_active': True}
        )

        if created:
            # Креирај чет соба за курсот ако не постои
            chat_room, room_created = ChatRoom.objects.get_or_create(
                course=course,
                defaults={
                    'name': f'Чет за {course.title}',
                    'room_type': 'course',
                    'created_by': course.instructor
                }
            )

            # Додај го корисникот во чет собата
            chat_room.participants.add(user)

            messages.success(request, f'Успешно се запишавте на курсот "{course.title}"!')
        else:
            if enrollment.is_active:
                messages.info(request, 'Веќе сте запишани на овој курс.')
            else:
                enrollment.is_active = True
                enrollment.save()
                messages.success(request, f'Повторно се активизиравте на курсот "{course.title}"!')

        return redirect('courses:detail', slug=course.slug)


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'courses/lesson_detail.html'
    context_object_name = 'lesson'

    def get_object(self):
        course_slug = self.kwargs['slug']
        lesson_id = self.kwargs['lesson_id']

        lesson = get_object_or_404(
            Lesson.objects.select_related('course'),
            id=lesson_id,
            course__slug=course_slug
        )

        # Провери дали корисникот има пристап
        user = self.request.user
        if not lesson.is_free:
            try:
                enrollment = Enrollment.objects.get(
                    student=user,
                    course=lesson.course,
                    is_active=True
                )
            except Enrollment.DoesNotExist:
                raise Http404("Немате пристап до оваа лекција.")

        return lesson

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object
        user = self.request.user

        # Сите лекции од курсот
        context['all_lessons'] = lesson.course.lessons.all().order_by('order')

        # Прогрес на лекцијата
        context['is_completed'] = False
        if user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(
                    student=user,
                    course=lesson.course,
                    is_active=True
                )
                lesson_progress, created = LessonProgress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=lesson
                )
                context['is_completed'] = lesson_progress.is_completed
                context['enrollment'] = enrollment
            except Enrollment.DoesNotExist:
                pass

        return context

    def post(self, request, *args, **kwargs):
        """Означи лекција како завршена"""
        lesson = self.get_object()
        user = request.user

        try:
            enrollment = Enrollment.objects.get(
                student=user,
                course=lesson.course,
                is_active=True
            )

            lesson_progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson
            )

            if not lesson_progress.is_completed:
                lesson_progress.is_completed = True
                lesson_progress.completed_at = timezone.now()
                lesson_progress.save()

                # Ажурирај го прогресот на целиот курс
                enrollment.update_progress()

                messages.success(request, 'Лекцијата е означена како завршена!')

        except Enrollment.DoesNotExist:
            messages.error(request, 'Грешка при ажурирање на прогресот.')

        return redirect('courses:lesson_detail', slug=lesson.course.slug, lesson_id=lesson.id)


# Instructor Views
class InstructorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type in ['instructor', 'admin']


class CourseCreateView(InstructorRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/create.html'

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        messages.success(self.request, 'Курсот е успешно креиран!')
        return super().form_valid(form)


class CourseUpdateView(InstructorRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/edit.html'

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Курсот е успешно ажуриран!')
        return super().form_valid(form)


class InstructorCoursesView(InstructorRequiredMixin, ListView):
    model = Course
    template_name = 'courses/instructor_courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(
            instructor=self.request.user
        ).annotate(
            enrolled_count=Count('enrollments', filter=Q(enrollments__is_active=True))
        ).order_by('-created_at')


class CourseManageView(InstructorRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/manage.html'
    context_object_name = 'course'

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object

        context['lessons'] = course.lessons.all().order_by('order')
        context['enrollments'] = Enrollment.objects.filter(
            course=course,
            is_active=True
        ).select_related('student').order_by('-enrolled_at')

        return context


class LessonCreateView(InstructorRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/add_lesson.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(
            Course,
            slug=self.kwargs['slug'],
            instructor=self.request.user
        )
        return context

    def form_valid(self, form):
        course = get_object_or_404(
            Course,
            slug=self.kwargs['slug'],
            instructor=self.request.user
        )
        form.instance.course = course

        # Автоматски постави го редниот број
        last_lesson = course.lessons.order_by('-order').first()
        form.instance.order = (last_lesson.order + 1) if last_lesson else 1

        messages.success(self.request, 'Лекцијата е успешно додадена!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('courses:manage', kwargs={'slug': self.kwargs['slug']})


class LessonUpdateView(InstructorRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/edit_lesson.html'
    pk_url_kwarg = 'lesson_id'

    def get_queryset(self):
        course_slug = self.kwargs['slug']
        return Lesson.objects.filter(course__slug=course_slug, course__instructor=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        return context

    def get_success_url(self):
        return reverse('courses:manage', kwargs={'slug': self.kwargs['slug']})


class CourseDeleteView(InstructorRequiredMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:my_courses')

    def get_queryset(self):
        # Дозволи само инструкторот да го брише својот курс
        return Course.objects.filter(instructor=self.request.user)

    def delete(self, request, *args, **kwargs):
        course = self.get_object()
        messages.success(request, f'Курсот "{course.title}" е успешно избришан!')
        return super().delete(request, *args, **kwargs)


class LessonDeleteView(InstructorRequiredMixin, DeleteView):
    model = Lesson
    template_name = 'courses/lesson_confirm_delete.html'
    pk_url_kwarg = 'lesson_id'

    def get_queryset(self):
        # Дозволи само инструкторот да ги брише лекциите од својот курс
        return Lesson.objects.filter(course__instructor=self.request.user)

    def get_success_url(self):
        # Врати го на manage страната на курсот
        return reverse_lazy('courses:manage', kwargs={'slug': self.object.course.slug})

    def delete(self, request, *args, **kwargs):
        lesson = self.get_object()
        messages.success(request, f'Лекцијата "{lesson.title}" е успешно избришана!')
        return super().delete(request, *args, **kwargs)