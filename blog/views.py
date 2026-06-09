from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Post, Profile
from .forms import (
    UserRegisterForm, ProfileUpdateForm, UserUpdateForm,
    EducationFormSet, CivilServiceFormSet, WorkExperienceFormSet, 
    VoluntaryWorkFormSet, TrainingProgramFormSet
)
from django.contrib.admin.views.decorators import staff_member_required

# 1. Read, replace 'home'
class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).order_by('-date_posted')
        return Post.objects.all().order_by('-date_posted')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

# 2. Read, replaced 'post_detail'
class PostDetailView(DetailView):
    model = Post

# 3. CREATE - Replaces 'post_create'
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'content', 'image']
    success_url = '/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

# 4. Update - Replaces 'post_update'
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content', 'image']
    success_url = '/' 

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    
# 5. DELETE - Replaces 'post_delete'
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

# --- FUNCTION BASED VIEWS ---

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Already log in into your account')
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('blog-home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'blog/register.html', {'form': form})

def about(request):
    return render(request, 'blog/about.html', {'title':'About'})

@login_required
def profile_update(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        # Pull all formsets with post request parameters
        edu_formset = EducationFormSet(request.POST, instance=profile)
        elig_formset = CivilServiceFormSet(request.POST, instance=profile)
        work_formset = WorkExperienceFormSet(request.POST, instance=profile)
        vol_formset = VoluntaryWorkFormSet(request.POST, instance=profile)
        train_formset = TrainingProgramFormSet(request.POST, instance=profile)
        
        # Verify absolute structural integrity before executing updates
        if (u_form.is_valid() and p_form.is_valid() and edu_formset.is_valid() and 
                elig_formset.is_valid() and work_formset.is_valid() and 
                vol_formset.is_valid() and train_formset.is_valid()):
            
            with transaction.atomic():
                u_form.save()
                p_form.save()
                edu_formset.save()
                elig_formset.save()
                work_formset.save()
                vol_formset.save()
                train_formset.save()
                
            messages.success(request, 'Your personal data sheets have been successfully recorded!')
            return redirect('user-profile', username=request.user.username)
        else:
            messages.error(request, 'Form validation failed. Review empty required fields or error components highlighted below.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
        
        # Clean loading parameters mapping directly to active parent ID instance
        edu_formset = EducationFormSet(instance=profile)
        elig_formset = CivilServiceFormSet(instance=profile)
        work_formset = WorkExperienceFormSet(instance=profile)
        vol_formset = VoluntaryWorkFormSet(instance=profile)
        train_formset = TrainingProgramFormSet(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'edu_formset': edu_formset,
        'elig_formset': elig_formset,
        'work_formset': work_formset,
        'vol_formset': vol_formset,
        'train_formset': train_formset,
    }
    return render(request, 'blog/profile_update.html', context)

def user_profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=profile_user).order_by('-date_posted')
    
    context = {
        'profile_user': profile_user,
        'posts': user_posts
    }
    return render(request, 'blog/user_profile.html', context)

@staff_member_required(login_url='login')
def custom_admin_dashboard(request):
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users
    }
    return render(request, 'blog/custom_admin.html', context)

@staff_member_required(login_url='login')
def toggle_user_status(request, user_id):
    user_to_toggle = get_object_or_404(User, id=user_id)
    
    if user_to_toggle.is_superuser:
        messages.warning(request, "You cannot deactivate a superuser.")
    else:
        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save()
        status = "activated" if user_to_toggle.is_active else "deactivated"
        messages.success(request, f"Account for {user_to_toggle.username} has been {status}.")
        
    return redirect('custom-admin')

