# courses/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Course, Enrollment, Lesson
from chat.models import ChatRoom


@receiver(post_save, sender=Course)
def create_course_chat_room(sender, instance, created, **kwargs):
    """Автоматски креирај чет соба за нов објавен курс"""
    if created and instance.status == 'published':
        chat_room = ChatRoom.objects.create(
            name=f'Чет за {instance.title}',
            room_type='course',
            course=instance,
            created_by=instance.instructor
        )
        chat_room.participants.add(instance.instructor)


@receiver(post_save, sender=Enrollment)
def add_student_to_course_chat(sender, instance, created, **kwargs):
    """Додај студент во чет собата на курсот кога се запишува"""
    if created and instance.is_active:
        try:
            chat_room = instance.course.chat_room
            chat_room.participants.add(instance.student)
        except ChatRoom.DoesNotExist:
            chat_room = ChatRoom.objects.create(
                name=f'Чет за {instance.course.title}',
                room_type='course',
                course=instance.course,
                created_by=instance.course.instructor
            )
            chat_room.participants.add(instance.course.instructor, instance.student)


@receiver(post_delete, sender=Enrollment)
def remove_student_from_course_chat(sender, instance, **kwargs):
    """Отстрани студент од чет собата кога се отпишува"""
    try:
        chat_room = instance.course.chat_room
        chat_room.participants.remove(instance.student)
    except (ChatRoom.DoesNotExist, ValueError):
        pass


@receiver(post_save, sender=Lesson)
def update_enrollments_on_new_lesson(sender, instance, created, **kwargs):
    """
    Кога се креира нова лекција, ажурирај го прогресот на сите запишани студенти
    и ресетирај го статусот "завршено" ако беше завршен курсот
    """
    if created:
        course = instance.course
        enrollments = Enrollment.objects.filter(
            course=course,
            is_active=True
        )

        for enrollment in enrollments:
            # 🆕 Ако курсот беше завршен, ресетирај го
            if enrollment.is_completed:
                enrollment.is_completed = False
                enrollment.completed_at = None
                enrollment.save()

            # Ажурирај го прогресот (ова ќе пресмета нов процент)
            enrollment.update_progress()


@receiver(post_delete, sender=Lesson)
def update_enrollments_on_lesson_delete(sender, instance, **kwargs):
    """
    Кога се брише лекција, ажурирај го прогресот на сите запишани студенти
    """
    course = instance.course
    enrollments = Enrollment.objects.filter(
        course=course,
        is_active=True
    )

    for enrollment in enrollments:
        enrollment.update_progress()