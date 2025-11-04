from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login, get_user_model
from django.views.generic import CreateView, TemplateView, UpdateView, ListView
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count
from .models import User, Profile
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm

User = get_user_model()


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




class AdminUserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view за листање на сите корисници"""
    model = User
    template_name = 'accounts/admin_users.html'
    context_object_name = 'users'
    paginate_by = 20

    def test_func(self):

        user = self.request.user
        print(f"\n{'=' * 50}")
        print(f"DEBUG - AdminUserListView.test_func()")
        print(f"Username: {user.username}")
        print(f"Is Staff: {user.is_staff}")
        print(f"Is Superuser: {user.is_superuser}")
        print(f"Test Result: {user.is_staff or user.is_superuser}")
        print(f"{'=' * 50}\n")

        return user.is_staff or user.is_superuser

    def handle_no_permission(self):
        print("Access Denied - handle_no_permission called")
        messages.error(self.request, 'Немате пристап до оваа страница. Само администратори имаат пристап.')
        return redirect('dashboard:home')

    def get_queryset(self):
        queryset = User.objects.all().annotate(
            courses_taught_count=Count('courses_taught'),
            enrollments_count=Count('enrollments')
        ).order_by('-date_joined')


        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )


        user_type = self.request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)


        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['instructors'] = User.objects.filter(user_type='instructor').count()
        context['students'] = User.objects.filter(user_type='student').count()
        context['search'] = self.request.GET.get('search', '')
        context['user_type_filter'] = self.request.GET.get('user_type', '')
        return context


class AdminDeleteUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Admin view за бришење на корисници"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, 'Немате пристап до оваа акција.')
        return redirect('dashboard:home')

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)


        if user == request.user:
            messages.error(request, 'Не можете да го избришете својот сопствен акаунт!')
            return redirect('accounts:admin_users')


        if user.is_superuser:
            messages.error(request, 'Не можете да бришете суперадминистратори!')
            return redirect('accounts:admin_users')

        username = user.username
        user.delete()
        messages.success(request, f'Корисникот "{username}" е успешно избришан!')
        return redirect('accounts:admin_users')


class AdminToggleUserStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Admin view за активација/деактивација на корисници"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, 'Немате пристап до оваа акција.')
        return redirect('dashboard:home')

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)


        if user == request.user:
            messages.error(request, 'Не можете да го менувате својот статус!')
            return redirect('accounts:admin_users')


        if user.is_superuser:
            messages.error(request, 'Не можете да го менувате статусот на суперадминистратори!')
            return redirect('accounts:admin_users')


        user.is_active = not user.is_active
        user.save()

        status = 'активиран' if user.is_active else 'деактивиран'
        messages.success(request, f'Корисникот "{user.username}" е {status}!')
        return redirect('accounts:admin_users')


class AdminUserDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin view за детален преглед на корисник"""
    template_name = 'accounts/admin_user_detail.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, 'Немате пристап до оваа страница.')
        return redirect('dashboard:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        profile, _ = Profile.objects.get_or_create(user=user)

        context['profile_user'] = user
        context['profile'] = profile


        if user.user_type == 'instructor':
            context['courses'] = user.courses_taught.all()
            context['total_students'] = sum(
                course.get_enrolled_count() for course in context['courses']
            )


        if user.user_type == 'student':
            context['enrollments'] = user.enrollments.all()
            context['completed_courses'] = user.enrollments.filter(is_completed=True).count()

        return context