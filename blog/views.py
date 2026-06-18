from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Post, Profile, Address
from .forms import (
    UserRegisterForm, ProfileUpdateForm, UserUpdateForm, AddressUpdateForm,
    EducationFormSet, CivilServiceFormSet, WorkExperienceFormSet,
    VoluntaryWorkFormSet, TrainingProgramFormSet,
)
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
import logging

logger = logging.getLogger(__name__)

# --- POST VIEWS (UNCHANGED) ---
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

class PostDetailView(DetailView):
    model = Post

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'content', 'image']
    success_url = '/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

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
            messages.success(request, 'Account created successfully.')
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('blog-home')
    else:
        form = UserRegisterForm()
    return render(request, 'blog/register.html', {'form': form})

def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})

@login_required
def profile_update(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    permanent_address, _ = Address.objects.get_or_create(
        user=request.user, address_type='Permanent'
    )
    residential_address, _ = Address.objects.get_or_create(
        user=request.user, address_type='Residential'
    )

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        perm_form = AddressUpdateForm(
            request.POST, instance=permanent_address, prefix='perm'
        )
        res_form = AddressUpdateForm(
            request.POST, instance=residential_address, prefix='res'
        )
        edu_formset   = EducationFormSet(request.POST, instance=profile)
        elig_formset  = CivilServiceFormSet(request.POST, instance=profile)
        work_formset  = WorkExperienceFormSet(request.POST, instance=profile)
        vol_formset   = VoluntaryWorkFormSet(request.POST, instance=profile)
        train_formset = TrainingProgramFormSet(request.POST, instance=profile)

        forms_valid = (
            u_form.is_valid()
            and p_form.is_valid()
            and perm_form.is_valid()
            and res_form.is_valid()
            and edu_formset.is_valid()
            and elig_formset.is_valid()
            and work_formset.is_valid()
            and vol_formset.is_valid()
            and train_formset.is_valid()
        )

        if forms_valid:
            with transaction.atomic():
                u_form.save()
                p_form.save()

                perm_obj = perm_form.save(commit=False)
                perm_obj.user = request.user
                perm_obj.address_type = 'Permanent'
                perm_obj.save()

                res_obj = res_form.save(commit=False)
                res_obj.user = request.user
                res_obj.address_type = 'Residential'
                res_obj.save()

                edu_formset.save()
                elig_formset.save()
                work_formset.save()
                vol_formset.save()
                train_formset.save()

            messages.success(request, 'Your PDS has been updated!')
            return redirect('user-profile', username=request.user.username)

        else:
            # ----------------------------------------------------------------
            # FIX: log every form's errors to the Django console.
            # This makes future debugging trivial — just check the terminal
            # output when a save fails instead of guessing which field broke.
            # ----------------------------------------------------------------
            def _log_errors(label, form_or_formset):
                if hasattr(form_or_formset, 'errors'):
                    errs = form_or_formset.errors
                    if errs:
                        logger.warning("PDS save blocked — %s errors: %s", label, errs)
                # formsets also have non_form_errors
                if hasattr(form_or_formset, 'non_form_errors'):
                    nfe = form_or_formset.non_form_errors()
                    if nfe:
                        logger.warning("PDS save blocked — %s non_form_errors: %s", label, nfe)

            _log_errors('u_form', u_form)
            _log_errors('p_form', p_form)
            _log_errors('perm_form', perm_form)
            _log_errors('res_form', res_form)
            _log_errors('edu_formset', edu_formset)
            _log_errors('elig_formset', elig_formset)
            _log_errors('work_formset', work_formset)
            _log_errors('vol_formset', vol_formset)
            _log_errors('train_formset', train_formset)

            messages.error(request, 'Validation failed. Please check your inputs.')

    else:
        u_form        = UserUpdateForm(instance=request.user)
        p_form        = ProfileUpdateForm(instance=profile)
        perm_form     = AddressUpdateForm(instance=permanent_address, prefix='perm')
        res_form      = AddressUpdateForm(instance=residential_address, prefix='res')
        edu_formset   = EducationFormSet(instance=profile)
        elig_formset  = CivilServiceFormSet(instance=profile)
        work_formset  = WorkExperienceFormSet(instance=profile)
        vol_formset   = VoluntaryWorkFormSet(instance=profile)
        train_formset = TrainingProgramFormSet(instance=profile)

    # Calculate age from birth_date if it exists
    from datetime import date as date_type
    calculated_age = None
    if profile.birth_date:
        today = date_type.today()
        bd = profile.birth_date
        calculated_age = today.year - bd.year - (
            (today.month, today.day) < (bd.month, bd.day)
        )

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'perm_form': perm_form,
        'res_form': res_form,
        'edu_formset': edu_formset,
        'elig_formset': elig_formset,
        'work_formset': work_formset,
        'vol_formset': vol_formset,
        'train_formset': train_formset,
        'calculated_age': calculated_age,
    }
    return render(request, 'blog/profile_update.html', context)

def user_profile_view(request, username):
    from datetime import date as date_type
    profile_user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=profile_user).order_by('-date_posted')
    can_view_full_pds = (request.user == profile_user or request.user.is_superuser)

    # Calculate age for display
    profile_age = None
    try:
        bd = profile_user.profile.birth_date
        if bd:
            today = date_type.today()
            profile_age = today.year - bd.year - (
                (today.month, today.day) < (bd.month, bd.day)
            )
    except Profile.DoesNotExist:
        pass

    context = {
        'profile_user': profile_user,
        'posts': user_posts,
        'can_view_full_pds': can_view_full_pds,
        'profile_age': profile_age,
    }
    return render(request, 'blog/user_profile.html', context)

@staff_member_required(login_url='login')
def custom_admin_dashboard(request):
    users = User.objects.select_related(
        'profile', 'profile__gender_3nf',
        'profile__civil_status_3nf', 'profile__citizenship_3nf'
    ).prefetch_related(
        'pds_addresses'
    ).annotate(
        total_education=Count('profile__education', distinct=True),
        total_work=Count('profile__work_experiences', distinct=True)
    ).order_by('-date_joined')

    return render(request, 'blog/custom_admin.html', {'users': users})


@staff_member_required(login_url='login')
def toggle_user_status(request, user_id):
    user_to_toggle = get_object_or_404(User, id=user_id)
    if user_to_toggle.is_superuser:
        messages.warning(request, "Cannot deactivate superuser.")
    else:
        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save()
        messages.success(request, f"User {user_to_toggle.username} status toggled.")
    return redirect('custom-admin')

@user_passes_test(lambda u: u.is_staff, login_url='login')
def pds_search(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        # Search across: first/last name, username, email, city, province, school, bio/position
        matching_users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(pds_addresses__city_municipality__icontains=query) |
            Q(pds_addresses__province__icontains=query) |
            Q(profile__education__school_name__icontains=query) |
            Q(profile__bio__icontains=query)
        ).distinct().select_related(
            'profile',
            'profile__gender_3nf',
            'profile__civil_status_3nf',
            'profile__citizenship_3nf',
            'profile__citizenship_acquisition_3nf',
        ).prefetch_related(
            'pds_addresses',
            'profile__education__level_3nf',
            'profile__eligibilities',
            'profile__work_experiences',
            'profile__voluntary_works',
            'profile__trainings',
            'profile__special_skills',
        )

        for user in matching_users:
            profile = getattr(user, 'profile', None)

            # Addresses
            addresses = list(user.pds_addresses.all())
            permanent = next((a for a in addresses if a.address_type == 'Permanent'), None)
            residential = next((a for a in addresses if a.address_type == 'Residential'), None)

            # One-to-many sections (empty list = N/A shown in template)
            education     = list(profile.education.all())        if profile else []
            eligibilities = list(profile.eligibilities.all())    if profile else []
            work_exp      = list(profile.work_experiences.all()) if profile else []
            vol_work      = list(profile.voluntary_works.all())  if profile else []
            trainings     = list(profile.trainings.all())        if profile else []
            skills        = list(profile.special_skills.all())   if profile else []

            # Calculate age from birth_date
            from datetime import date as date_type
            age = None
            if profile and profile.birth_date:
                today = date_type.today()
                bd = profile.birth_date
                age = today.year - bd.year - (
                    (today.month, today.day) < (bd.month, bd.day)
                )

            results.append({
                'user': user,
                'profile': profile,
                'permanent': permanent,
                'residential': residential,
                'education': education,
                'eligibilities': eligibilities,
                'work_exp': work_exp,
                'vol_work': vol_work,
                'trainings': trainings,
                'skills': skills,
                'age': age,
            })

    return render(request, 'blog/pds_search.html', {
        'query': query,
        'results': results,
    })
