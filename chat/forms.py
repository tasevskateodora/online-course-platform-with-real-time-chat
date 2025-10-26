# chat/forms.py

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import ChatRoom, Message
from courses.models import Course
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatRoomForm(forms.ModelForm):
    # Додај ново поле за избор на корисници
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Додај корисници во собата'
    )

    class Meta:
        model = ChatRoom
        fields = ['name', 'room_type', 'course', 'participants']
        labels = {
            'name': 'Име на собата',
            'room_type': 'Тип на соба',
            'course': 'Курс (за курс соби)'
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Внесете име на собата'
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'course': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Ограничи ги курсевите на оние што ги има корисникот
        if user and user.user_type == 'instructor':
            self.fields['course'].queryset = Course.objects.filter(
                instructor=user,
                status='published'
            ).exclude(chat_room__isnull=False)

            # Прикажи ги сите активни корисници освен креаторот
            self.fields['participants'].queryset = User.objects.filter(
                is_active=True
            ).exclude(id=user.id).order_by('first_name', 'last_name', 'username')

            print(f"DEBUG: Број на корисници: {self.fields['participants'].queryset.count()}")
        else:
            self.fields['course'].queryset = Course.objects.none()
            self.fields['participants'].queryset = User.objects.none()

        # Сокриј го полето за курс ако не е потребно
        self.fields['course'].required = False

    def clean(self):
        cleaned_data = super().clean()
        room_type = cleaned_data.get('room_type')
        course = cleaned_data.get('course')

        if room_type == 'course' and not course:
            raise forms.ValidationError(
                'За курс соби морате да изберете курс.'
            )

        if room_type != 'course' and course:
            cleaned_data['course'] = None

        return cleaned_data


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Напишете ја вашата порака...',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('content'),
            Submit('submit', 'Испрати', css_class='btn btn-primary mt-2')
        )


class QuickMessageForm(forms.Form):
    """Брза форма за испраќање пораки преку AJAX"""
    message = forms.CharField(
        max_length=1000,
        widget=forms.TextInput(attrs={
            'placeholder': 'Напишете порака...',
            'class': 'form-control',
            'autocomplete': 'off'
        })
    )


class FileMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'file_attachment']
        labels = {
            'content': 'Опис (опционално)',
            'file_attachment': 'Прикачи фајл'
        }
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': 'Опис на фајлот...',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('file_attachment', css_class='form-control mb-2'),
            Field('content', css_class='form-control mb-2'),
            Submit('submit', 'Прикачи фајл', css_class='btn btn-success')
        )