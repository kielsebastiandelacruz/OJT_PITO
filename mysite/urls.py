"""
URL configuration for mysite project.
"""

from django.urls import path, include
from django.contrib.auth import views as auth_views
from blog import views as blog_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    # path('admin/', admin.site.urls),  # Django admin disabled as requested

    # Registration & Authentication
    path('register/', blog_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='blog/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='blog/logout.html'), name='logout'),
    
    # Password Reset (No admin intervention needed)
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='blog/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='blog/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='blog/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='blog/password_reset_complete.html'), name='password_reset_complete'),
    
    # Third-party / App routes
    path('accounts/', include('allauth.urls')),
    path('', include('blog.urls')),

    # Custom Admin Control Paths
    path('custom-admin/', blog_views.custom_admin_dashboard, name='custom-admin'),
    path('custom-admin/toggle/<int:user_id>/', blog_views.toggle_user_status, name='toggle-status'),
    path('custom-admin/pds-search/', blog_views.pds_search, name='pds-search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)