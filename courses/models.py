# courses/models.py

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    DIFFICULTY_CHOICES = (
        ('beginner', 'Почетник'),
        ('intermediate', 'Средно'),
        ('advanced', 'Напредно'),
    )

    STATUS_CHOICES = (
        ('draft', 'Нацрт'),
        ('published', 'Објавен'),
        ('archived', 'Архивиран'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=250)
    description = models.TextField()
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_taught'
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    duration_hours = models.PositiveIntegerField(help_text="Должина во часови")
    max_students = models.PositiveIntegerField(null=True, blank=True)
    requirements = models.TextField(blank=True, help_text="Предуслови за курсот")
    what_you_learn = models.TextField(help_text="Што ќе научат студентите")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            # Генерирај slug од наслов
            base_slug = slugify(self.title, allow_unicode=False)

            # Ако е празен (само кирилични букви), користи UUID
            if not base_slug or base_slug == '-':
                base_slug = f'course-{uuid.uuid4().hex[:8]}'

            # Провери уникатност
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk if self.pk else None).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('courses:detail', kwargs={'slug': self.slug})

    def get_enrolled_count(self):
        return self.enrollments.filter(is_active=True).count()

    def get_completion_rate(self):
        total_enrollments = self.enrollments.filter(is_active=True).count()
        if total_enrollments == 0:
            return 0
        completed = self.enrollments.filter(is_completed=True).count()
        return (completed / total_enrollments) * 100

    def __str__(self):
        return self.title


class Lesson(models.Model):
    LESSON_TYPE_CHOICES = (
        ('video', 'Видео'),
        ('text', 'Текст'),
        ('quiz', 'Квиз'),
        ('assignment', 'Задача'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='lesson_videos/', blank=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES)
    order = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField(default=0)
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.FloatField(default=0.0)

    class Meta:
        unique_together = ['student', 'course']

    def get_progress(self):
        total_lessons = self.course.lessons.count()
        if total_lessons == 0:
            return 0
        completed_lessons = LessonProgress.objects.filter(
            enrollment=self,
            is_completed=True
        ).count()
        return (completed_lessons / total_lessons) * 100

    def update_progress(self):
        self.progress_percentage = self.get_progress()
        if self.progress_percentage >= 100:
            self.is_completed = True
            if not self.completed_at:
                from django.utils import timezone
                self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['enrollment', 'lesson']

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.lesson.title}"