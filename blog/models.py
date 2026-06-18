from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

# --- BLOG APP MODELS ---
def user_directory_path(instance, filename):
    username = instance.author.username if instance.author else 'anonymous'
    return os.path.join('post_pics', username, filename)


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(null=True, blank=True, upload_to=user_directory_path)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})

@receiver(post_delete, sender=Post)
def delete_post_image(sender, instance, **kwargs):
    if instance.image and instance.image.name != 'default.jpg':
        instance.image.delete(save=False)

# --- 3NF LOOKUP TABLES ---
class GenderLookup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: db_table = 'pds_lu_gender'
    def __str__(self): return self.name

class CivilStatusLookup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: db_table = 'pds_lu_civil_status'
    def __str__(self): return self.name

class CitizenshipLookup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta: db_table = 'pds_lu_citizenship'
    def __str__(self): return self.name

class CitizenshipAcqLookup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta: db_table = 'pds_lu_citizenship_acquisition'
    def __str__(self): return self.name

class EducationLevelLookup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta: db_table = 'pds_lu_education_level'
    def __str__(self): return self.name

# --- CORE PDS TABLE ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    bio = models.TextField(max_length=500, blank=True, help_text="Short description")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Date of Birth")

    gender_3nf = models.ForeignKey(GenderLookup, on_delete=models.SET_NULL, null=True, blank=True)
    civil_status_3nf = models.ForeignKey(CivilStatusLookup, on_delete=models.SET_NULL, null=True, blank=True)
    citizenship_3nf = models.ForeignKey(CitizenshipLookup, on_delete=models.SET_NULL, null=True, blank=True)
    citizenship_acquisition_3nf = models.ForeignKey(CitizenshipAcqLookup, on_delete=models.SET_NULL, null=True, blank=True)

    middle_name = models.CharField(max_length=100, blank=True, null=True)
    name_extension = models.CharField(max_length=20, blank=True, null=True)
    place_of_birth = models.CharField(max_length=255, blank=True, null=True)
    employee_number = models.CharField(max_length=50, blank=True, null=True)
    dual_citizenship_country = models.CharField(max_length=100, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta: db_table = 'pds_personal_information'
    def __str__(self): return f'{self.user.username} Profile'

# --- SPECIAL SKILLS (extracted from Profile) ---
class SpecialSkill(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='special_skills')
    skill = models.CharField(max_length=255)
    class Meta: db_table = 'pds_special_skills'
    def __str__(self): return f'{self.skill} ({self.profile.user.username})'

# --- ADDRESS TABLE ---
class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('Residential', 'Residential'),
        ('Permanent', 'Permanent'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pds_addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default='Residential')
    house_block_lot = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    subdivision_village = models.CharField(max_length=100, blank=True, null=True)
    barangay = models.CharField(max_length=100, blank=True, null=True)
    city_municipality = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    class Meta: db_table = 'pds_addresses'
    def __str__(self): return f'{self.address_type} – {self.user.username}'

# --- EDUCATION ---
class Education(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='education')
    level_3nf = models.ForeignKey(EducationLevelLookup, on_delete=models.SET_NULL, null=True, blank=True)
    school_name = models.CharField(max_length=255)
    degree_finished = models.CharField(max_length=255, blank=True, null=True)
    class Meta: db_table = 'pds_educational_background'

# Eligibility
class CivilServiceEligibility(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='eligibilities')
    eligibility_type = models.CharField(max_length=255)
    license_number = models.CharField(max_length=100, default='N/A')
    valid_until = models.DateField(blank=True, null=True)
    class Meta: db_table = 'pds_civil_service'

# Work experince
class WorkExperience(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='work_experiences')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    position_title = models.CharField(max_length=150)
    company_agency = models.CharField(max_length=255)
    status_of_appointment = models.CharField(max_length=100)
    government_service = models.BooleanField(default=False)
    class Meta: db_table = 'pds_work_experience'

# Voluntary Work
class VoluntaryWork(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='voluntary_works')
    organization_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    number_of_hours = models.PositiveIntegerField(blank=True, null=True)
    position = models.CharField(max_length=150)
    class Meta: db_table = 'pds_voluntary_work'

# Training Program
class TrainingProgram(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='trainings')
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)           # FIX: was non-nullable
    number_of_hours = models.PositiveIntegerField(blank=True, null=True)  # FIX: was non-nullable
    training_type = models.CharField(max_length=100)
    sponsor = models.CharField(max_length=255)
    class Meta: db_table = 'pds_learning_development'
    