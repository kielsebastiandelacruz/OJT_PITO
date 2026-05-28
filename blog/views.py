from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Post, Profile
from .forms import UserRegisterForm, ProfileUpdateForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

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
        # This links the user to the post so the folder name is generated
        form.instance.author = self.request.user
        return super().form_valid(form)

# 4. Update - Replaces 'post_update'
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content', 'image']
    
    # 1. This ensures that after the save is successful, you land on the feed
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

        if self.request.user == post.author:
            return True
        return False

# --- FUNCTION BASED VIEWS ---

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, 'Already log in into your account')
            login(request, user)
            return redirect('blog-home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'blog/register.html', {'form': form})

# Keep your 'about' function as it is—sometimes FBVs are simpler for static pages!
def about(request):
    return render(request, 'blog/about.html', {'title':'About'})

@login_required
def profile_update(request):
    # This automatically fetches or builds a profile row if missing
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile picture has been updated!')
            return redirect('blog-home')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'blog/profile_update.html', {'form': form})
