from django.contrib import admin
from .models import Post, Profile, Education, CivilServiceEligibility, WorkExperience, VoluntaryWork, TrainingProgram

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date_posted')
    search_fields = ('title', 'content')
    list_filter = ('date_posted', 'author')
    readonly_fields = ('date_posted',)

admin.site.register(Post, PostAdmin)

# --- PDS Inlines for Profile ---
class EducationInline(admin.TabularInline):
    model = Education
    extra = 1

class CivilServiceInline(admin.TabularInline):
    model = CivilServiceEligibility
    extra = 1

class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 1

class VoluntaryWorkInline(admin.TabularInline):
    model = VoluntaryWork
    extra = 1

class TrainingProgramInline(admin.TabularInline):
    model = TrainingProgram
    extra = 1

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'citizenship')
    search_fields = ('user__username', 'user__email', 'mobile_number')
    # This renders the 1:N forms directly inside the Profile view
    inlines = [EducationInline, CivilServiceInline, WorkExperienceInline, VoluntaryWorkInline, TrainingProgramInline]