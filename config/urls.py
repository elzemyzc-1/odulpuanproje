from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from accounts.views import register, home
from django.shortcuts import redirect

# Root URL redirection to login
def redirect_to_login(request):
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # accounts uygulamasını projeye dahil et
    
    # Root URL redirects to login
    path('', redirect_to_login),
    
    # Login and logout at root level
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login', template_name=None), name='logout'),
    path('register/', register, name='register'),
    
]
