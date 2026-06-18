from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import (
    Post, Profile, Address, Education, CivilServiceEligibility,
    WorkExperience, VoluntaryWork, TrainingProgram,
    GenderLookup, EducationLevelLookup,
    CivilStatusLookup, CitizenshipLookup, CitizenshipAcqLookup
)

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username']

# ---------------------------------------------------------------------------
# Shared date widget — plain text input that accepts mm/dd/yyyy.
# We intentionally avoid type="date" because browsers always submit it as
# yyyy-mm-dd regardless of locale, which conflicts with the mm/dd/yyyy
# display format the PDS uses everywhere.
# ---------------------------------------------------------------------------

MMDDYYYY_ATTRS = {'placeholder': 'mm/dd/yyyy', 'class': 'mmddyyyy-input'}

class MMDDYYYYDateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('input_formats', ['%m/%d/%Y'])
        kwargs.setdefault('widget', forms.DateInput(format='%m/%d/%Y', attrs=MMDDYYYY_ATTRS))
        super().__init__(*args, **kwargs)

# --- CORE PROFILE FORM (3NF Updated) ---
class ProfileUpdateForm(forms.ModelForm):
    birth_date = MMDDYYYYDateField(required=True, label="Date of Birth")

    gender_3nf = forms.ModelChoiceField(
        queryset=GenderLookup.objects.none(),
        required=True,
        label="Sex at Birth",
        empty_label="Select Sex at Birth",
    )

    # Civil Status — seeded from CivilStatusLookup
    civil_status_3nf = forms.ModelChoiceField(
        queryset=CivilStatusLookup.objects.none(),
        required=False,
        label="Civil Status",
        empty_label="Select Civil Status",
    )

    # Citizenship — only two allowed values
    citizenship_3nf = forms.ModelChoiceField(
        queryset=CitizenshipLookup.objects.none(),
        required=False,
        label="Citizenship",
        empty_label="Select Citizenship",
    )

    # Citizenship acquisition — shown when Filipino is selected
    citizenship_acquisition_3nf = forms.ModelChoiceField(
        queryset=CitizenshipAcqLookup.objects.none(),
        required=False,
        label="If Filipino, by",
        empty_label="Select acquisition",
    )

    # Dual citizenship country — shown when Dual Citizenship is selected
    dual_citizenship_country = forms.CharField(
        required=False,
        label="Specify other country",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. United States'}),
    )

    class Meta:
        model = Profile
        fields = [
            'image', 'bio', 'birth_date', 'gender_3nf',
            'civil_status_3nf', 'citizenship_3nf',
            'citizenship_acquisition_3nf', 'dual_citizenship_country',
            'middle_name', 'name_extension',
            'employee_number', 'mobile_number',
        ]
        labels = {'bio': 'Position'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mobile_number'].required = True
        self.fields['name_extension'].required = False

        # Gender
        GenderLookup.objects.get_or_create(name='Male')
        GenderLookup.objects.get_or_create(name='Female')
        self.fields['gender_3nf'].queryset = GenderLookup.objects.filter(
            name__in=['Male', 'Female']
        )

        # Civil Status — seed all five options
        for status in ['Single', 'Married', 'Widowed', 'Separated', 'Others']:
            CivilStatusLookup.objects.get_or_create(name=status)
        self.fields['civil_status_3nf'].queryset = CivilStatusLookup.objects.filter(
            name__in=['Single', 'Married', 'Widowed', 'Separated', 'Others']
        )

        # Citizenship — seed two options
        for c in ['Filipino', 'Dual Citizenship']:
            CitizenshipLookup.objects.get_or_create(name=c)
        self.fields['citizenship_3nf'].queryset = CitizenshipLookup.objects.filter(
            name__in=['Filipino', 'Dual Citizenship']
        )

        # Citizenship acquisition — seed two options
        for acq in ['By Birth', 'By Naturalization']:
            CitizenshipAcqLookup.objects.get_or_create(name=acq)
        self.fields['citizenship_acquisition_3nf'].queryset = CitizenshipAcqLookup.objects.filter(
            name__in=['By Birth', 'By Naturalization']
        )

# --- ADDRESS FORM (used twice: Permanent and Residential) ---
class AddressUpdateForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'province', 'city_municipality', 'barangay', 'zip_code',
            'subdivision_village', 'street', 'house_block_lot',
        ]
        labels = {
            'province':            'Province',
            'city_municipality':   'City / Municipality',
            'barangay':            'Barangay',
            'zip_code':            'Zip Code',
            'subdivision_village': 'Subdivision / Village',
            'street':              'Street',
            'house_block_lot':     'House / Block / Lot',
        }
        widgets = {
            'province':            forms.TextInput(attrs={'id_prefix': 'province',      'autocomplete': 'off'}),
            'city_municipality':   forms.TextInput(attrs={'id_prefix': 'city_municipality', 'autocomplete': 'off'}),
            'barangay':            forms.TextInput(attrs={'id_prefix': 'barangay',      'autocomplete': 'off'}),
            'zip_code':            forms.TextInput(attrs={'autocomplete': 'off', 'placeholder': 'Auto-filled', 'readonly': 'readonly'}),
            'subdivision_village': forms.TextInput(),
            'street':              forms.TextInput(),
            'house_block_lot':     forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

# User Form
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

# --- ALL 5 ONE-TO-MANY PDS INLINE FORMSETS ---

# Education: level_3nf is a ForeignKey to EducationLevelLookup. Per spec
# the dropdown must only offer: College, Masters, Doctorate,
# Vocational/Trade Course. We restrict the queryset the same way as
# gender above, rather than hardcoding plain-text choices, so the FK
# integrity is preserved.
ALLOWED_EDUCATION_LEVELS = ['College', 'Masters', 'Doctorate', 'Vocational/Trade Course']

def _get_education_level_queryset():
    """
    Ensures the four allowed education level rows exist in the DB, then
    returns a queryset filtered to exactly those rows.

    Called at class-definition time (module import) so the queryset is
    always fully populated — not lazily deferred. This eliminates the
    'This field is required' error that occurred because the class-level
    queryset=none() placeholder was sometimes used during formset POST
    validation before __init__ could override it.
    """
    for lvl in ALLOWED_EDUCATION_LEVELS:
        EducationLevelLookup.objects.get_or_create(name=lvl)
    return EducationLevelLookup.objects.filter(name__in=ALLOWED_EDUCATION_LEVELS)

class EducationForm(forms.ModelForm):
    # ROOT CAUSE FIX: queryset is set eagerly at class definition time, not
    # lazily in __init__. This guarantees the ModelChoiceField always has
    # a populated queryset during both GET rendering AND POST validation,
    # preventing the 'This field is required' false-positive on existing rows.
    level_3nf = forms.ModelChoiceField(
        queryset=_get_education_level_queryset(),
        required=True,
        label="Level",
        empty_label="Select Level",
    )

    class Meta:
        model = Education
        fields = ('level_3nf', 'school_name', 'degree_finished')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['degree_finished'].required = False
        self.fields['school_name'].required = True

class CivilServiceForm(forms.ModelForm):
    valid_until = MMDDYYYYDateField(
        required=False,
        label="Valid Until",
    )

    class Meta:
        model = CivilServiceEligibility
        fields = ('eligibility_type', 'license_number', 'valid_until')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eligibility_type'].required = True
        # license_number defaults to 'N/A' on the model — optional on form
        self.fields['license_number'].required = False

class WorkExperienceForm(forms.ModelForm):
    start_date = MMDDYYYYDateField(required=True, label="Start Date")
    end_date = MMDDYYYYDateField(required=False, label="End Date")

    class Meta:
        model = WorkExperience
        fields = (
            'start_date', 'end_date', 'position_title',
            'company_agency', 'status_of_appointment',
        )

class VoluntaryWorkForm(forms.ModelForm):
    start_date = MMDDYYYYDateField(required=True, label="Start Date")
    end_date = MMDDYYYYDateField(required=False, label="End Date")

    class Meta:
        model = VoluntaryWork
        fields = (
            'organization_name', 'start_date', 'end_date',
            'number_of_hours', 'position',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['number_of_hours'].required = False

class TrainingProgramForm(forms.ModelForm):
    start_date = MMDDYYYYDateField(required=True, label="Start Date")
    end_date = MMDDYYYYDateField(required=False, label="End Date")

    class Meta:
        model = TrainingProgram
        fields = (
            'title', 'start_date', 'end_date',
            'number_of_hours', 'training_type', 'sponsor',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['number_of_hours'].required = False
        self.fields['end_date'].required = False

# Inline formsets
EducationFormSet = inlineformset_factory(
    Profile, Education,
    form=EducationForm,
    extra=0,
    can_delete=True,
    can_delete_extra=True,
)

CivilServiceFormSet = inlineformset_factory(
    Profile, CivilServiceEligibility,
    form=CivilServiceForm,
    extra=0,
    can_delete=True,
    can_delete_extra=True,
)

WorkExperienceFormSet = inlineformset_factory(
    Profile, WorkExperience,
    form=WorkExperienceForm,
    extra=0,
    can_delete=True,
    can_delete_extra=True,
)

VoluntaryWorkFormSet = inlineformset_factory(
    Profile, VoluntaryWork,
    form=VoluntaryWorkForm,
    extra=0,
    can_delete=True,
    can_delete_extra=True,
)

TrainingProgramFormSet = inlineformset_factory(
    Profile, TrainingProgram,
    form=TrainingProgramForm,
    extra=0,
    can_delete=True,
    can_delete_extra=True,
)
