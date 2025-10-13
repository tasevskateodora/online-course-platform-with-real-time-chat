# courses/forms.py

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field, Fieldset, HTML
from .models import Course, Lesson, Category


class CourseSearchForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Пребарајте курсеви...',
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Сите категории",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    difficulty = forms.ChoiceField(
        choices=[('', 'Сите нивоа')] + list(Course.DIFFICULTY_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    price = forms.ChoiceField(
        choices=[
            ('', 'Сите курсеви'),
            ('free', 'Бесплатни'),
            ('paid', 'Платени')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sort = forms.ChoiceField(
        choices=[
            ('-created_at', 'Најнови'),
            ('title', 'По име (А-Ш)'),
            ('-enrolled_count', 'Најпопуларни'),
            ('price', 'По цена (најниска)')
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'category', 'thumbnail', 'price',
            'difficulty', 'duration_hours', 'max_students',
            'requirements', 'what_you_learn', 'status'
        ]
        labels = {
            'title': 'Наслов на курсот',
            'description': 'Опис',
            'category': 'Категорија',
            'thumbnail': 'Слика за курсот',
            'price': 'Цена (во денари)',
            'difficulty': 'Ниво на тежина',
            'duration_hours': 'Должина (во часови)',
            'max_students': 'Максимален број студенти',
            'requirements': 'Предуслови',
            'what_you_learn': 'Што ќе научат студентите',
            'status': 'Статус'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 3}),
            'what_you_learn': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'duration_hours': forms.NumberInput(attrs={'min': 1}),
            'max_students': forms.NumberInput(attrs={'min': 1})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Основни информации',
                Row(
                    Column('title', css_class='form-group col-md-8 mb-3'),
                    Column('status', css_class='form-group col-md-4 mb-3'),
                    css_class='form-row'
                ),
                Field('description', css_class='form-control mb-3'),
                Row(
                    Column('category', css_class='form-group col-md-6 mb-3'),
                    Column('difficulty', css_class='form-group col-md-6 mb-3'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Детали за курсот',
                Row(
                    Column('price', css_class='form-group col-md-4 mb-3'),
                    Column('duration_hours', css_class='form-group col-md-4 mb-3'),
                    Column('max_students', css_class='form-group col-md-4 mb-3'),
                    css_class='form-row'
                ),
                Field('thumbnail', css_class='form-control mb-3'),
            ),
            Fieldset(
                'Содржина',
                Field('requirements', css_class='form-control mb-3'),
                Field('what_you_learn', css_class='form-control mb-3'),
            ),
            Submit('submit', 'Зачувај курс', css_class='btn btn-primary btn-lg')
        )


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            'title', 'content', 'lesson_type', 'video_url', 'video_file',
            'duration_minutes', 'is_free'
        ]
        labels = {
            'title': 'Наслов на лекцијата',
            'content': 'Содржина на лекцијата',
            'lesson_type': 'Тип на лекција',
            'video_url': 'URL на видео (YouTube, Vimeo, итн.)',
            'video_file': 'Прикачи видео фајл',
            'duration_minutes': 'Должина (во минути)',
            'is_free': 'Бесплатен преглед'
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6}),
            'duration_minutes': forms.NumberInput(attrs={'min': 1}),
            'video_url': forms.URLInput(attrs={'placeholder': 'https://youtube.com/watch?v=...'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('title', css_class='form-control mb-3'),
            Field('lesson_type', css_class='form-control mb-3'),
            Row(
                Column('duration_minutes', css_class='form-group col-md-6 mb-3'),
                Column(
                    Field('is_free'),
                    HTML('<label class="form-check-label ms-2">Дозволи бесплатен преглед</label>'),
                    css_class='form-group col-md-6 mb-3 d-flex align-items-center'
                ),
                css_class='form-row'
            ),
            Field('content', css_class='form-control mb-3'),
            HTML('<hr>'),
            HTML('<h6>Видео содржина</h6>'),
            HTML(
                '<p class="text-muted small">Можете да внесете URL на видео или да прикачите видео фајл. URL има приоритет.</p>'),
            Field('video_url', css_class='form-control mb-3'),
            Field('video_file', css_class='form-control mb-3'),
            Submit('submit', 'Зачувај лекција', css_class='btn btn-success btn-lg')
        )

    def clean(self):
        cleaned_data = super().clean()
        lesson_type = cleaned_data.get('lesson_type')
        video_url = cleaned_data.get('video_url')
        video_file = cleaned_data.get('video_file')
        content = cleaned_data.get('content')

        # Валидација за видео лекции
        if lesson_type == 'video':
            if not video_url and not video_file:
                raise forms.ValidationError(
                    'За видео лекции морате да внесете URL или да прикачите видео фајл.'
                )

        # Валидација за текст лекции
        if lesson_type == 'text':
            if not content:
                raise forms.ValidationError(
                    'За текст лекции морате да внесете содржина.'
                )

        return cleaned_data


class QuickEnrollForm(forms.Form):
    """Брза форма за запишување на курс"""
    pass