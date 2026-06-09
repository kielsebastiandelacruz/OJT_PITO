from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Post, Profile

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username']  # Passwords are included automatically by UserCreationForm

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        # We mapped your existing bio, birth_date, and gender alongside the new PDS fields
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
        # Force the core identity fields to be required on the frontend to prevent incomplete PDS
        required_fields = ['birth_date', 'place_of_birth', 'gender', 'civil_status', 'mobile_number']
        for field in required_fields:
            self.fields[field].required = True

    def clean(self):
        cleaned_data = super().clean()
        citizenship = cleaned_data.get('citizenship')
        dual_citizenship_country = cleaned_data.get('dual_citizenship_country')

        # Custom Validation: If Dual Citizen is selected, country must be provided
        if citizenship == 'D' and not dual_citizenship_country:
            self.add_error('dual_citizenship_country', 'Please specify the country for dual citizenship.')
        
        return cleaned_data

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']