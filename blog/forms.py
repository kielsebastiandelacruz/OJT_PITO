from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import Post, Profile, Education, CivilServiceEligibility, WorkExperience, VoluntaryWork, TrainingProgram

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'image', 'bio', 'birth_date', 'gender', 
            'middle_name', 'name_extension', 'place_of_birth', 
            'civil_status', 'employee_number', 'citizenship', 
            'dual_citizenship_country', 'citizenship_acquisition', 
            'house_block_lot', 'street', 'subdivision_village', 
            'barangay', 'city_municipality', 'province', 
            'mobile_number', 'number_of_children', 'special_skills_hobbies'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ['birth_date', 'place_of_birth', 'gender', 'civil_status', 'mobile_number']
        for field in required_fields:
            self.fields[field].required = True

    def clean(self):
        cleaned_data = super().clean()
        citizenship = cleaned_data.get('citizenship')
        dual_citizenship_country = cleaned_data.get('dual_citizenship_country')

        if citizenship == 'D' and not dual_citizenship_country:
            self.add_error('dual_citizenship_country', 'Please specify the country for dual citizenship.')
        
        return cleaned_data

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    # Explicitly make first and last name required for the PDS
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = User
        # Add first_name and last_name here
        fields = ['username', 'first_name', 'last_name', 'email']

# --- ALL 5 ONE-TO-MANY PDS INLINE FORMSETS ---
EducationFormSet = inlineformset_factory(
    Profile, Education, 
    fields=('level', 'school_name', 'degree_finished'), 
    extra=1, can_delete=True
)

CivilServiceFormSet = inlineformset_factory(
    Profile, CivilServiceEligibility, 
    fields=('eligibility_type', 'license_number', 'valid_until'), 
    widgets={'valid_until': forms.DateInput(attrs={'type': 'date'})},
    extra=1, can_delete=True
)

WorkExperienceFormSet = inlineformset_factory(
    Profile, WorkExperience, 
    fields=('start_date', 'end_date', 'position_title', 'company_agency', 'status_of_appointment', 'government_service'), 
    widgets={
        'start_date': forms.DateInput(attrs={'type': 'date'}),
        'end_date': forms.DateInput(attrs={'type': 'date'}),
    },
    extra=1, can_delete=True
)

VoluntaryWorkFormSet = inlineformset_factory(
    Profile, VoluntaryWork, 
    fields=('organization_name', 'start_date', 'end_date', 'number_of_hours', 'position'), 
    widgets={
        'start_date': forms.DateInput(attrs={'type': 'date'}),
        'end_date': forms.DateInput(attrs={'type': 'date'}),
    },
    extra=1, can_delete=True
)

TrainingProgramFormSet = inlineformset_factory(
    Profile, TrainingProgram, 
    fields=('title', 'start_date', 'end_date', 'number_of_hours', 'training_type', 'sponsor'), 
    widgets={
        'start_date': forms.DateInput(attrs={'type': 'date'}),
        'end_date': forms.DateInput(attrs={'type': 'date'}),
    },
    extra=1, can_delete=True
)
