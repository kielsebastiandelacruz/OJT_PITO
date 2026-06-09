from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

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

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
    ('P', 'Prefer not to say'),
)

# --- 1:1 PROFILE EXTENSION ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    # --- EXISTING FIELDS (Retained for zero data loss, adapted for PDS) ---
    bio = models.TextField(max_length=500, blank=True, help_text="Short description about yourself")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name="Sex at Birth")

    # --- NEW PDS FIELDS: I. Personal Information ---
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    name_extension = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., Jr., Sr., III")
    place_of_birth = models.CharField(max_length=255, blank=True, null=True)

    CIVIL_STATUS_CHOICES = [
        ('S', 'Single'), ('M', 'Married'), ('W', 'Widowed'), 
        ('SEP', 'Separated'), ('O', 'Others')
    ]
    civil_status = models.CharField(max_length=3, choices=CIVIL_STATUS_CHOICES, blank=True, null=True)
    employee_number = models.CharField(max_length=50, blank=True, null=True)

    CITIZENSHIP_CHOICES = [('F', 'Filipino'), ('D', 'Dual Citizenship')]
    citizenship = models.CharField(max_length=1, choices=CITIZENSHIP_CHOICES, default='F')
    dual_citizenship_country = models.CharField(max_length=100, blank=True, null=True)
    citizenship_acquisition = models.CharField(
        max_length=20, 
        choices=[('B', 'By Birth'), ('N', 'By Naturalization')], 
        blank=True, null=True
    )

    # Address
    house_block_lot = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    subdivision_village = models.CharField(max_length=100, blank=True, null=True)
    barangay = models.CharField(max_length=100, blank=True, null=True)
    city_municipality = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    
    mobile_number = models.CharField(max_length=20, blank=True, null=True)

    # --- II. Family Background ---
    number_of_children = models.PositiveIntegerField(default=0, blank=True, null=True)

    # --- VIII. Other Information ---
    special_skills_hobbies = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

# --- 1:N PDS TABLES ---
class Education(models.Model):
    LEVEL_CHOICES = [
        ('HS', 'High School'), ('COL', 'College'), 
        ('VOC', 'Vocational/Technical'), ('MAS', 'Master\'s Degree'), 
        ('DOC', 'Doctorate Degree')
    ]
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='education')
    level = models.CharField(max_length=3, choices=LEVEL_CHOICES)
    school_name = models.CharField(max_length=255)
    degree_finished = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.profile.user.username} - {self.get_level_display()}"

class CivilServiceEligibility(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='eligibilities')
    eligibility_type = models.CharField(max_length=255, help_text="e.g., Career Service, RA 1080")
    license_number = models.CharField(max_length=100, blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)

class WorkExperience(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='work_experiences')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text="Leave blank if currently employed")
    position_title = models.CharField(max_length=150)
    company_agency = models.CharField(max_length=255)
    status_of_appointment = models.CharField(max_length=100)
    government_service = models.BooleanField(default=False)

class VoluntaryWork(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='voluntary_works')
    organization_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    number_of_hours = models.PositiveIntegerField(blank=True, null=True)
    position = models.CharField(max_length=150)

class TrainingProgram(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='trainings')
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_hours = models.PositiveIntegerField()
    training_type = models.CharField(max_length=100, help_text="Managerial, Supervisory, Technical, etc.")
    sponsor = models.CharField(max_length=255)
