from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import University, Member, Owner, Accommodation, Specialist, Campus
from datetime import date

@receiver(post_migrate, dispatch_uid="core.create_initial_data")
def create_initial_data(sender, **kwargs):
    if sender.name == 'core':
        # Create universities
        hku, created = University.objects.get_or_create(name='HKU', defaults={'country': 'China', 'address': 'Hong Kong'})
        hkust, created = University.objects.get_or_create(name='HKUST', defaults={'country': 'China', 'address': 'Hong Kong'})
        cuhk, created = University.objects.get_or_create(name='CUHK', defaults={'country': 'China', 'address': 'Hong Kong'})

        # Create members
        peter, created = Member.objects.get_or_create(name='Peter', defaults={'email': 'peter@hku.hk', 'phone': '12345678', 'university': hku})

        # Create owners
        george, created = Owner.objects.get_or_create(name='George', defaults={'email': 'george@example.com', 'phone': '88888888', 'address': 'Hong Kong'})
        ian, created = Owner.objects.get_or_create(name='Ian', defaults={'email': 'ian@example.com', 'phone': '99999999', 'address': 'Hong Kong'})

        # Create accommodations
        a_building, created = Accommodation.objects.get_or_create(name='A Building', defaults={
            'building_name': 'A Building',
            'description': 'Apartment for HKU and HKUST students',
            'type': 'Apartment',
            'num_bedrooms': 2,
            'num_beds': 4,
            'address': 'Hong Kong',
            'latitude': 22.28405,
            'longitude': 114.13784,
            'available_from': date(2025, 1, 1),
            'available_to': date(2026, 1, 1),
            'monthly_rent': 5000,
            'owner': george,
            'is_available': True
        })
        a_building.universities.add(hku, hkust)

        b_building, created = Accommodation.objects.get_or_create(name='B Building', defaults={
            'building_name': 'B Building',
            'description': 'Apartment for HKU students',
            'type': 'Apartment',
            'num_bedrooms': 2,
            'num_beds': 4,
            'address': 'Hong Kong',
            'latitude': 22.28405,
            'longitude': 114.13784,
            'available_from': date(2025, 1, 1),
            'available_to': date(2026, 1, 1),
            'monthly_rent': 5000,
            'owner': george,
            'is_available': True
        })
        b_building.universities.add(hku)

        c_building, created = Accommodation.objects.get_or_create(name='C Building', defaults={
            'building_name': 'C Building',
            'description': 'Apartment for HKUST students',
            'type': 'Apartment',
            'num_bedrooms': 2,
            'num_beds': 4,
            'address': 'Hong Kong',
            'latitude': 22.33584,
            'longitude': 114.26355,
            'available_from': date(2025, 1, 1),
            'available_to': date(2026, 1, 1),
            'monthly_rent': 5000,
            'owner': ian,
            'is_available': True
        })
        c_building.universities.add(hkust)

        # Create specialists
        yu, created = Specialist.objects.get_or_create(name='Yu', defaults={'email': 'yu@hku.hk', 'phone': '55555555', 'university': hku})
        tao, created = Specialist.objects.get_or_create(name='Tao', defaults={'email': 'tao@hkust.hk', 'phone': '66666666', 'university': hkust})

        # Create campuses
        Campus.objects.get_or_create(name='Main Campus', university=hku, defaults={'latitude': 22.28405, 'longitude': 114.13784})
        Campus.objects.get_or_create(name='Sassoon Road Campus', university=hku, defaults={'latitude': 22.2675, 'longitude': 114.12881})
        Campus.objects.get_or_create(name='Swire Institute of Marine Science', university=hku, defaults={'latitude': 22.20805, 'longitude': 114.26021})
        Campus.objects.get_or_create(name='Kadoorie Centre', university=hku, defaults={'latitude': 22.43022, 'longitude': 114.11429})
        Campus.objects.get_or_create(name='Faculty of Dentistry', university=hku, defaults={'latitude': 22.28649, 'longitude': 114.14426})

        Campus.objects.get_or_create(name='Main Campus', university=hkust, defaults={'latitude': 22.33584, 'longitude': 114.26355})

        Campus.objects.get_or_create(name='Main Campus', university=cuhk, defaults={'latitude': 22.41907, 'longitude': 114.20693})