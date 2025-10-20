# courses/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Course, Enrollment
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

        # Додај го инструкторот како учесник
        chat_room.participants.add(instance.instructor)


@receiver(post_save, sender=Enrollment)
def add_student_to_course_chat(sender, instance, created, **kwargs):
    """Додај студент во чет собата на курсот кога се запишува"""
    if created and instance.is_active:
        try:
            chat_room = instance.course.chat_room
            chat_room.participants.add(instance.student)
        except ChatRoom.DoesNotExist:
            # Ако нема чет соба, креирај ја
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



