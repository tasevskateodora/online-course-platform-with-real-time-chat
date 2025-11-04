# courses/forms.py

from django import forms
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
        empty_label='Сите категории',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    difficulty = forms.ChoiceField(
        choices=[('', 'Сите нивоа')] + list(Course.DIFFICULTY_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    price = forms.ChoiceField(
        choices=[
            ('', 'Сите цени'),
            ('free', 'Бесплатно'),
            ('paid', 'Платени'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    sort = forms.ChoiceField(
        choices=[
            ('-created_at', 'Најнови прво'),
            ('title', 'Наслов (А-Ш)'),
            ('-enrolled_count', 'Најпопуларни'),
            ('price', 'Цена (ниска-висока)'),
            ('-price', 'Цена (висока-ниска)'),
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'category', 'thumbnail', 'price',
            'difficulty', 'duration_hours', 'max_students',
            'requirements', 'what_you_learn'
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
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': '0.01', 'class': 'form-control'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'duration_hours': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'max_students': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'what_you_learn': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            'title', 'lesson_type', 'content', 'video_url', 'video_file', 'pdf_file',
            'duration_minutes',
        ]
        labels = {
            'title': 'Наслов на лекцијата',
            'content': 'Содржина на лекцијата',
            'lesson_type': 'Тип на лекција',
            'video_url': 'URL на видео',
            'video_file': 'Прикачи видео фајл',
            'pdf_file': 'Прикачи PDF документ',
            'duration_minutes': 'Должина (во минути)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'lesson_type': forms.Select(attrs={'class': 'form-select'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'video_file': forms.FileInput(attrs={'class': 'form-control'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'duration_minutes': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        lesson_type = cleaned_data.get('lesson_type')
        video_url = cleaned_data.get('video_url')
        video_file = cleaned_data.get('video_file')
        pdf_file = cleaned_data.get('pdf_file')
        content = cleaned_data.get('content')


        if lesson_type == 'video':
            if not video_url and not video_file:
                raise forms.ValidationError(
                    'За видео лекции морате да внесете URL или да прикачите видео фајл.'
                )


        if lesson_type == 'pdf':
            if not pdf_file:
                raise forms.ValidationError(
                    'За PDF лекции морате да прикачите PDF документ.'
                )


        if lesson_type == 'text':
            if not content:
                raise forms.ValidationError(
                    'За текст лекции морате да внесете содржина.'
                )

        return cleaned_data