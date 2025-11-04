from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [

    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),


    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/<str:username>/', views.PublicProfileView.as_view(), name='public_profile'),

path('admin/users/', views.AdminUserListView.as_view(), name='admin_users'),
    path('admin/users/<int:user_id>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:user_id>/delete/', views.AdminDeleteUserView.as_view(), name='admin_delete_user'),
    path('admin/users/<int:user_id>/toggle-status/', views.AdminToggleUserStatusView.as_view(), name='admin_toggle_status'),



    path('password-change/',
         auth_views.PasswordChangeView.as_view(
             template_name='accounts/password_change.html',
             success_url='/accounts/profile/'
         ),
         name='password_change'),
]
