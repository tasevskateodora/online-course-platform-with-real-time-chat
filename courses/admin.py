from django.contrib import admin
from .models import Category, Course, Lesson, Enrollment, LessonProgress


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'status', 'price', 'created_at')
    list_filter = ('status', 'difficulty', 'category', 'created_at')
    search_fields = ('title', 'instructor__username')
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Основни информации', {
            'fields': ('title', 'slug', 'description', 'instructor', 'category')
        }),
        ('Детали', {
            'fields': ('thumbnail', 'price', 'difficulty', 'status', 'duration_hours', 'max_students')
        }),
        ('Содржина', {
            'fields': ('requirements', 'what_you_learn')
        }),
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'lesson_type', 'order', 'duration_minutes')
    list_filter = ('lesson_type', 'is_free')
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'is_active', 'progress_percentage')
    list_filter = ('is_active', 'is_completed', 'enrolled_at')
    search_fields = ('student__username', 'course__title')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'is_completed', 'time_spent_minutes')
    list_filter = ('is_completed',)
