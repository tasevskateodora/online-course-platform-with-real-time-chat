from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.views.generic import CreateView, TemplateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import User, Profile
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard:home')


class LogoutPageView(TemplateView):
    """Страна што се прикажува после одјава"""
    template_name = 'accounts/logout.html'


class CustomLogoutView(TemplateView):
    """Custom logout view што прифаќа GET барања"""
    template_name = 'accounts/logout.html'

    def get(self, request, *args, **kwargs):
        from django.contrib.auth import logout
        logout(request)
        messages.success(request, 'Успешно се одјавивте од вашата сметка.')
        return super().get(request, *args, **kwargs)


class RegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f'Добредојде {self.object.username}!')
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Креирај профил ако не постои
        profile, created = Profile.objects.get_or_create(user=user)

        context['user'] = user
        context['profile'] = profile
        context['enrollments'] = user.enrollments.filter(is_active=True)
        return context


class ProfileEditView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, created = Profile.objects.get_or_create(user=self.request.user)

        context['user_form'] = UserUpdateForm(instance=self.request.user)
        context['profile_form'] = ProfileUpdateForm(instance=profile)
        return context

    def post(self, request, *args, **kwargs):
        profile, created = Profile.objects.get_or_create(user=request.user)

        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Вашиот профил е успешно ажуриран!')
            return redirect('accounts:profile')

        context = {
            'user_form': user_form,
            'profile_form': profile_form
        }
        return render(request, self.template_name, context)


class PublicProfileView(TemplateView):
    template_name = 'accounts/public_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = kwargs['username']
        user = get_object_or_404(User, username=username)
        profile, created = Profile.objects.get_or_create(user=user)

        context['profile_user'] = user
        context['profile'] = profile

        # Ако е инструктор, прикажи ги неговите курсеви
        if user.user_type == 'instructor':
            context['courses'] = user.courses_taught.filter(status='published')

        return context