# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import User, Profile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label='Име')
    last_name = forms.CharField(max_length=30, required=True, label='Презиме')
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        required=True,
        label='Тип на корисник'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.fields['username'].label = 'Корисничко име'
        self.fields['username'].help_text = 'Задолжително. 150 или помалку знаци. Единствено букви, бројки и @/./+/-/_.'
        self.fields['email'].label = 'Е-пошта'
        self.fields['password1'].label = 'Лозинка'
        self.fields['password1'].help_text = 'Вашата лозинка мора да содржи најмалку 8 карактери.'
        self.fields['password2'].label = 'Потврди лозинка'
        self.fields['password2'].help_text = 'Внесете ја истата лозинка како претходно, за верификација.'


        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'user_type':
                field.widget.attrs['class'] = 'form-select'


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture', 'phone_number']
        labels = {
            'username': 'Корисничко име',
            'email': 'Е-пошта',
            'first_name': 'Име',
            'last_name': 'Презиме',
            'bio': 'Биографија',
            'profile_picture': 'Профилна слика',
            'phone_number': 'Телефонски број',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('phone_number', css_class='form-control mb-3'),
            Field('profile_picture', css_class='form-control mb-3'),
            Field('bio', css_class='form-control mb-3'),
            Submit('submit', 'Ажурирај профил', css_class='btn btn-primary')
        )


class ProfileUpdateForm(forms.ModelForm):
    skills = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Одвоете ги вештините со запирка (пр: Python, Django, JavaScript)"
    )

    class Meta:
        model = Profile
        fields = ['location', 'website', 'linkedin', 'github', 'skills']
        labels = {
            'location': 'Локација',
            'website': 'Веб-страница',
            'linkedin': 'LinkedIn профил',
            'github': 'GitHub профил',
            'skills': 'Вештини',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('location', css_class='form-control mb-3'),
            Field('website', css_class='form-control mb-3'),
            Row(
                Column('linkedin', css_class='form-group col-md-6 mb-3'),
                Column('github', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('skills', css_class='form-control mb-3'),
        )