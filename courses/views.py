import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.utils import timezone

from .models import Course, Category, Lesson, Enrollment, LessonProgress, Quiz, Question, Answer, QuizAttempt, \
    StudentAnswer
from .forms import CourseForm, LessonForm
from .ai_quiz_generator import extract_text_from_pdf, generate_quiz_from_text


# --- MIXINS ---
class InstructorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.user_type in ['instructor', 'admin'])


# --- КУРС ПРИКАЗИ ---
class CourseListView(ListView):
    model = Course
    template_name = 'courses/list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        queryset = Course.objects.filter(status='published').select_related('instructor', 'category')

        # 🔍 Филтрирање по пребарување
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(instructor__first_name__icontains=search_query) |
                Q(instructor__last_name__icontains=search_query)
            )

        # 📁 Филтрирање по категорија
        category_id = self.request.GET.get('category', '').strip()
        if category_id:
            try:
                queryset = queryset.filter(category_id=int(category_id))
            except ValueError:
                pass

        # 📊 Филтрирање по ниво на тежина
        difficulty = self.request.GET.get('difficulty', '').strip()
        if difficulty in ['beginner', 'intermediate', 'advanced']:
            queryset = queryset.filter(difficulty=difficulty)

        # 💰 Филтрирање по цена
        price_filter = self.request.GET.get('price', '').strip()
        if price_filter == 'free':
            queryset = queryset.filter(price=0)
        elif price_filter == 'paid':
            queryset = queryset.filter(price__gt=0)

        # 🔀 Сортирање
        sort_by = self.request.GET.get('sort', '-created_at').strip()
        valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'title', '-title']
        if sort_by in valid_sorts:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')

        print(f"🔍 Search: {search_query}")
        print(f"📁 Category: {category_id}")
        print(f"📊 Difficulty: {difficulty}")
        print(f"💰 Price: {price_filter}")
        print(f"🔀 Sort: {sort_by}")
        print(f"📋 Results: {queryset.count()}")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_difficulty'] = self.request.GET.get('difficulty', '')
        context['selected_price'] = self.request.GET.get('price', '')
        context['selected_sort'] = self.request.GET.get('sort', '-created_at')
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user, course=self.object, is_active=True
            ).exists()
        context['lessons'] = self.object.lessons.all().order_by('order')
        return context


class CourseManageView(InstructorRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/manage.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lessons'] = self.object.lessons.all().select_related('quiz').order_by('order')
        context['enrollments'] = self.object.enrollments.all().select_related('student')
        return context


class CourseCreateView(InstructorRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/create.html'

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('courses:instructor_courses')


class CourseUpdateView(InstructorRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/edit.html'

    def get_success_url(self):
        return reverse('courses:manage', kwargs={'slug': self.object.slug})


class CourseDeleteView(InstructorRequiredMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('courses:instructor_courses')


# --- ЛЕКЦИЈА ПРИКАЗИ ---
class LessonCreateView(InstructorRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/add_lesson.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, slug=self.kwargs['slug'])
        return context

    def form_valid(self, form):
        course = get_object_or_404(Course, slug=self.kwargs['slug'], instructor=self.request.user)
        form.instance.course = course

        # Автоматски сетирај го order ако не е сетиран
        if not form.instance.order:
            # Земи го следниот достапен број
            last_lesson = course.lessons.order_by('-order').first()
            form.instance.order = (last_lesson.order + 1) if last_lesson else 1

        messages.success(self.request, f'Лекцијата "{form.instance.title}" е успешно додадена!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('courses:manage', kwargs={'slug': self.kwargs['slug']})


class LessonUpdateView(InstructorRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/edit_lesson.html'
    pk_url_kwarg = 'lesson_id'

    def get_object(self):
        return get_object_or_404(
            Lesson,
            id=self.kwargs['lesson_id'],
            course__slug=self.kwargs['slug'],
            course__instructor=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        context['lesson'] = self.object
        return context

    def get_success_url(self):
        return reverse('courses:manage', kwargs={'slug': self.object.course.slug})


class LessonDeleteView(InstructorRequiredMixin, DeleteView):
    model = Lesson
    template_name = 'courses/lesson_confirm_delete.html'

    def get_object(self):
        return get_object_or_404(Lesson, id=self.kwargs['lesson_id'], course__slug=self.kwargs['slug'])

    def get_success_url(self):
        return reverse('courses:manage', kwargs={'slug': self.kwargs['slug']})


class LessonDetailView(LoginRequiredMixin, View):
    """Прикажи лекција и дозволи да се означи како завршена"""

    def get(self, request, slug, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id, course__slug=slug)
        course = lesson.course

        # Провери дали е запишан
        enrollment = None
        is_completed = False

        if request.user.user_type == 'student':
            enrollment = Enrollment.objects.filter(
                student=request.user,
                course=course,
                is_active=True
            ).first()

            if enrollment:
                # Провери дали лекцијата е завршена
                progress = LessonProgress.objects.filter(
                    enrollment=enrollment,
                    lesson=lesson
                ).first()
                is_completed = progress.is_completed if progress else False

        # Најди ја следната и претходната лекција
        all_lessons = course.lessons.all().order_by('order')
        next_lesson = all_lessons.filter(order__gt=lesson.order).first()
        prev_lesson = all_lessons.filter(order__lt=lesson.order).last()

        context = {
            'lesson': lesson,
            'quiz_obj': Quiz.objects.filter(lesson=lesson).first(),
            'all_lessons': all_lessons,
            'next_lesson': next_lesson,  # 🆕 НОВО
            'prev_lesson': prev_lesson,  # 🆕 НОВО
            'enrollment': enrollment,
            'is_completed': is_completed,
        }

        return render(request, 'courses/lesson_detail.html', context)

    def post(self, request, slug, lesson_id):
        """Означи лекција како завршена"""
        lesson = get_object_or_404(Lesson, id=lesson_id, course__slug=slug)

        # Само студенти можат да означуваат лекции како завршени
        if request.user.user_type != 'student':
            messages.warning(request, 'Само студентите можат да означуваат лекции како завршени.')
            return redirect('courses:lesson_detail', slug=slug, lesson_id=lesson_id)

        # Провери дали е запишан
        enrollment = Enrollment.objects.filter(
            student=request.user,
            course=lesson.course,
            is_active=True
        ).first()

        if not enrollment:
            messages.error(request, 'Морате да се запишете на курсот за да можете да означувате лекции.')
            return redirect('courses:detail', slug=slug)

        # Креирај или ажурирај прогрес
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )

        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()

            # Ажурирај го вкупниот прогрес
            enrollment.update_progress()

            messages.success(request, f'✅ Лекцијата "{lesson.title}" е означена како завршена!')
        else:
            messages.info(request, 'Оваа лекција е веќе означена како завршена.')

        return redirect('courses:lesson_detail', slug=slug, lesson_id=lesson_id)


# --- КВИЗ ЛОГИКА (QuizTake, QuizSubmit, QuizResult) ---

class QuizTakeView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'courses/quiz_take.html'
    pk_url_kwarg = 'quiz_id'
    context_object_name = 'quiz'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ВАЖНО: Ги праќаме прашањата со prefetch за да ги добиеме и одговорите
        context['questions'] = self.object.questions.prefetch_related('answers').all()
        return context


class QuizSubmitView(LoginRequiredMixin, View):
    def post(self, request, slug, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        questions = quiz.questions.all()
        score = 0
        total = questions.count()

        attempt = QuizAttempt.objects.create(
            quiz=quiz, student=request.user, score=0, max_score=total
        )

        for question in questions:
            ans_id = request.POST.get(f'question_{question.id}')
            if ans_id:
                answer = get_object_or_404(Answer, id=ans_id)
                if answer.is_correct: score += 1
                StudentAnswer.objects.create(
                    attempt=attempt, question=question,
                    selected_answer=answer, is_correct=answer.is_correct
                )

        final_score = (score / total) * 100 if total > 0 else 0
        attempt.score = final_score
        attempt.passed = final_score >= quiz.passing_score
        attempt.save()
        return redirect('courses:quiz_result', slug=slug, attempt_id=attempt.id)


class QuizResultView(LoginRequiredMixin, DetailView):
    model = QuizAttempt
    template_name = 'courses/quiz_result.html'
    context_object_name = 'attempt'

    def get_object(self):
        return get_object_or_404(QuizAttempt, id=self.kwargs['attempt_id'], student=self.request.user)


# --- AI ГЕНЕРАТОР ---

class GenerateQuizView(InstructorRequiredMixin, View):
    def post(self, request, slug, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id, course__slug=slug)
        Quiz.objects.filter(lesson=lesson).delete()

        quiz_text = ""
        if lesson.lesson_type == 'pdf' and lesson.pdf_file:
            quiz_text = extract_text_from_pdf(lesson.pdf_file)
        if not quiz_text or len(quiz_text) < 10:
            quiz_text = f"Title: {lesson.title}. Content: {lesson.content}"

        try:
            raw_response = generate_quiz_from_text(quiz_text)
            if raw_response:
                if isinstance(raw_response, str):
                    if "```json" in raw_response:
                        raw_response = raw_response.split("```json")[1].split("```")[0].strip()
                    quiz_data = json.loads(raw_response)
                else:
                    quiz_data = raw_response

                q_list = quiz_data.get('questions') or quiz_data.get('quiz')
                if q_list:
                    quiz = Quiz.objects.create(lesson=lesson, title=f"Квиз: {lesson.title}")
                    for idx, q_item in enumerate(q_list, 1):
                        q_txt = q_item.get('question_text') or q_item.get('question')
                        if q_txt:
                            question = Question.objects.create(quiz=quiz, question_text=q_txt, order=idx)
                            ans_list = q_item.get('answers') or q_item.get('options')
                            for a_idx, a_item in enumerate(ans_list, 1):
                                Answer.objects.create(
                                    question=question,
                                    answer_text=a_item.get('answer_text') or a_item.get('text'),
                                    is_correct=bool(a_item.get('is_correct') or a_item.get('correct')),
                                    order=a_idx
                                )
                    messages.success(request, "Квизот е успешно генериран!")
            else:
                messages.error(request, "AI не врати податоци.")
        except Exception as e:
            messages.error(request, f"Грешка: {str(e)}")
        return redirect('courses:manage', slug=slug)


# --- ОСТАНАТО ---

class InstructorCoursesView(InstructorRequiredMixin, ListView):
    model = Course
    template_name = 'courses/instructor_courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)


class EnrollCourseView(LoginRequiredMixin, View):
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug)
        Enrollment.objects.get_or_create(student=request.user, course=course, defaults={'is_active': True})
        return redirect('courses:detail', slug=slug)