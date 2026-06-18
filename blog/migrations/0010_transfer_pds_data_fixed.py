from django.db import migrations

def transfer_data(apps, schema_editor):
    Profile = apps.get_model('blog', 'Profile')
    Education = apps.get_model('blog', 'Education')
    
    GenderLookup = apps.get_model('blog', 'GenderLookup')
    CivilStatusLookup = apps.get_model('blog', 'CivilStatusLookup')
    CitizenshipLookup = apps.get_model('blog', 'CitizenshipLookup')
    CitizenshipAcqLookup = apps.get_model('blog', 'CitizenshipAcqLookup')
    EducationLevelLookup = apps.get_model('blog', 'EducationLevelLookup')

    # 1. Transfer Profile Fields
    for profile in Profile.objects.all():
        if profile.gender:
            gender_obj, _ = GenderLookup.objects.get_or_create(name=profile.gender.strip())
            profile.gender_3nf = gender_obj
            
        if profile.civil_status:
            status_obj, _ = CivilStatusLookup.objects.get_or_create(name=profile.civil_status.strip())
            profile.civil_status_3nf = status_obj
            
        if profile.citizenship:
            citizen_obj, _ = CitizenshipLookup.objects.get_or_create(name=profile.citizenship.strip())
            profile.citizenship_3nf = citizen_obj
            
        if profile.citizenship_acquisition:
            acq_obj, _ = CitizenshipAcqLookup.objects.get_or_create(name=profile.citizenship_acquisition.strip())
            profile.citizenship_acquisition_3nf = acq_obj
            
        profile.save()

    # 2. Transfer Education Fields
    for edu in Education.objects.all():
        if edu.level:
            level_obj, _ = EducationLevelLookup.objects.get_or_create(name=edu.level.strip())
            edu.level_3nf = level_obj
            edu.save()

def reverse_transfer(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0009_remove_profile_barangay_and_more'), 
    ]
    operations = [
        migrations.RunPython(transfer_data, reverse_transfer),
    ]
    