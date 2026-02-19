from django.contrib import admin
from .models import Category, Course, Lesson, Enrollment, LessonProgress, Quiz, Question, Answer, QuizAttempt, StudentAnswer

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'status', 'price', 'created_at')
    list_filter = ('status', 'difficulty', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'lesson_type', 'order')
    list_filter = ('lesson_type', 'course')
    search_fields = ('title', 'content')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'is_completed', 'progress_percentage')
    list_filter = ('is_completed', 'course')

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    # Избришано 'time_spent_minutes' бидејќи го нема во моделот
    list_display = ('enrollment', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'lesson__course')

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # Избришани 'question_type' и 'points' бидејќи ги тргнавме од моделот
    list_display = ('question_text', 'quiz', 'order')
    list_filter = ('quiz',)
    inlines = [AnswerInline]

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'passing_score', 'created_at')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'max_score', 'passed', 'completed_at')
    list_filter = ('passed', 'quiz')

admin.site.register(Answer)
admin.site.register(StudentAnswer)