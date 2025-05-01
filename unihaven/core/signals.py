from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import University, Member, Owner, Accommodation, Specialist, Campus, Reservation
from .utils import AddressLookupService  # Import the lookup_address function
from datetime import date

@receiver(post_migrate, dispatch_uid="core.create_initial_data")
def create_initial_data(sender, **kwargs):
    if sender.name == 'core':
        # Create universities
        hku, created = University.objects.get_or_create(name='HKU', defaults={'country': 'China', 'address': 'Hong Kong'})
        hkust, created = University.objects.get_or_create(name='HKUST', defaults={'country': 'China', 'address': 'Hong Kong'})
        cuhk, created = University.objects.get_or_create(name='CUHK', defaults={'country': 'China', 'address': 'Hong Kong'})

        # Create owners
        george, created = Owner.objects.get_or_create(name='George', defaults={'email': 'george@example.com', 'phone': '88888888', 'address': 'Hong Kong'})
        ian, created = Owner.objects.get_or_create(name='Ian', defaults={'email': 'ian@example.com', 'phone': '99999999', 'address': 'Hong Kong'})

        # Create accommodations with dynamic geolocation
        # Jolly Villa
        JV_location = AddressLookupService.lookup_address("Jolly Villa")
        JV_latitude = JV_location['latitude'] if JV_location else 22.27731
        JV_longitude = JV_location['longitude'] if JV_location else 114.19238
        JV_geo_address = JV_location['geo_address'] if JV_location else "3786015386T20050430"
        
        JV, created = Accommodation.objects.get_or_create(
            name='Jolly Villa',
            defaults={
                'building_name': 'Jolly Villa',
                'description': 'Apartment for HKU students',
                'type': 'Apartment',
                'num_bedrooms': 2,
                'num_beds': 4,
                'room_number': 1, 
                'flat_number': 'C',
                'floor_number': 3,
                'address': 'Room 1, Flat C, Floor 3, Jolly Villa',
                'available_from': date(2025, 3, 1),
                'available_to': date(2025, 8, 31),
                'monthly_rent': 5000,
                'owner': george,
                'is_available': True,
                'latitude': JV_latitude,
                'longitude': JV_longitude,
                'geo_address': JV_geo_address
            }
        )
        JV.universities.add(hku, hkust)

        # South View Garden
        SVG_location = AddressLookupService.lookup_address("South View Garden")
        SVG_latitude = SVG_location['latitude'] if SVG_location else 22.27731
        SVG_longitude = SVG_location['longitude'] if SVG_location else 114.19238
        SVG_geo_address = SVG_location['geo_address'] if SVG_location else "3786015386T20050430"
        
        SVG, created = Accommodation.objects.get_or_create(
            name='South View Garden',
            defaults={
                'building_name': 'South View Garden',
                'description': 'Apartment for HKU students',
                'type': 'Apartment',
                'num_bedrooms': 2,
                'num_beds': 4,
                # 'room_number': , 
                'flat_number': 'G',
                'floor_number': 22,
                'address': 'Flat G, Floor 22, South View Garden',
                'available_from': date(2025, 4, 1),
                'available_to': date(2025, 10, 31),
                'monthly_rent': 5000,
                'owner': george,
                'is_available': True,
                'latitude': SVG_latitude,
                'longitude': SVG_longitude,
                'geo_address': SVG_geo_address
            }
        )
        SVG.universities.add(hku)

        # Glen Haven
        GH_location = AddressLookupService.lookup_address("Glen Haven")
        GH_latitude = GH_location['latitude'] if GH_location else 22.27731
        GH_longitude = GH_location['longitude'] if GH_location else 114.19238
        GH_geo_address = GH_location['geo_address'] if GH_location else "3786015386T20050430"
        
        GH, created = Accommodation.objects.get_or_create(
            name='Glen Haven',
            defaults={
                'building_name': 'Glen Haven',
                'description': 'Apartment for HKU and CUHK students',
                'type': 'Apartment',
                'room_number': 3, 
                'flat_number': 'E',
                'floor_number': 12,
                'num_bedrooms': 2,
                'num_beds': 4,
                'address': 'Room 3, Flat E, Glen Haven',
                'available_from': date(2025, 1, 1),
                'available_to': date(2025, 12, 31),
                'monthly_rent': 5000,
                'owner': ian,
                'is_available': True,
                'latitude': GH_latitude,
                'longitude': GH_longitude,
                'geo_address': GH_geo_address
            }
        )
        GH.universities.add(hku, cuhk)

        # Prosperity Mansion
        PM_location = AddressLookupService.lookup_address("Prosperity Mansion")
        PM_latitude = PM_location['latitude'] if PM_location else 22.27731
        PM_longitude = PM_location['longitude'] if PM_location else 114.19238
        PM_geo_address = PM_location['geo_address'] if PM_location else "3786015386T20050430"
        
        PM, created = Accommodation.objects.get_or_create(
            name='Prosperity Mansion',
            defaults={
                'building_name': 'Prosperity Mansion',
                'description': 'Apartment for CUHK students',
                'type': 'Apartment',
                # 'room_number': 1, 
                'flat_number': 'D',
                'floor_number': 2,
                'num_bedrooms': 2,
                'num_beds': 4,
                'address': 'Flat D, Prosperity Mansion',
                'available_from': date(2025, 3, 15),
                'available_to': date(2025, 7, 31),
                'monthly_rent': 5000,
                'owner': ian,
                'is_available': True,
                'latitude': PM_latitude,
                'longitude': PM_longitude,
                'geo_address': PM_geo_address
            }
        )
        PM.universities.add(cuhk)

        # Create specialists
        AnsonLee, created = Member.objects.get_or_create(
            name='Anson Lee',
            email='ansonlee@gmail.com',
            phone='2290 4324',
            university=hku
        )
        CandyChan, created = Member.objects.get_or_create(
            name='Tao',
            email='candychan@gmail.com',
            phone='3528 6925',
            university=hkust
        )

        BillyJohnson, created = Member.objects.get_or_create(
            name='Billy Johnson',
            email='billyjohnson@gmail.com',
            phone='3910 1481',
            university=cuhk
        )

        FredLam = Member.objects.create(
            name='Fred Lam',
            email='fredlam@gmail.com',
            phone='3859 4679',
            university=hku
        )

        # Create Reservations
        Reservation.objects.get_or_create(
            accommodation=SVG,
            member=AnsonLee,
            reserved_from=date(2025, 4, 15),
            reserved_to=date(2025, 4, 21),
            status='Confirmed',
        )

        Reservation.objects.get_or_create(
            accommodation=JV,
            member=AnsonLee,
            reserved_from=date(2025, 4, 22),
            reserved_to=date(2025, 5, 14),
            status='Confirmed',
        )

        Reservation.objects.get_or_create(
            accommodation=JV,
            member=AnsonLee,
            reserved_from=date(2025, 6, 15),
            reserved_to=date(2025, 6, 30),
            status='Cancelled',
        )

        Reservation.objects.get_or_create(
            accommodation=GH,
            member=CandyChan,
            reserved_from=date(2025, 5, 22),
            reserved_to=date(2025, 7, 7),
            status='Confirmed',
        )

        Reservation.objects.get_or_create(
            accommodation=GH,
            member=BillyJohnson,
            reserved_from=date(2025, 3, 1),
            reserved_to=date(2025, 5, 7),
            status='Confirmed',
        )


        # Create campuses
        Campus.objects.get_or_create(name='Main Campus', university=hku, defaults={'latitude': 22.28405, 'longitude': 114.13784})
        Campus.objects.get_or_create(name='Sassoon Road Campus', university=hku, defaults={'latitude': 22.2675, 'longitude': 114.12881})
        Campus.objects.get_or_create(name='Swire Institute of Marine Science', university=hku, defaults={'latitude': 22.20805, 'longitude': 114.26021})
        Campus.objects.get_or_create(name='Kadoorie Centre', university=hku, defaults={'latitude': 22.43022, 'longitude': 114.11429})
        Campus.objects.get_or_create(name='Faculty of Dentistry', university=hku, defaults={'latitude': 22.28649, 'longitude': 114.14426})

        Campus.objects.get_or_create(name='Main Campus', university=hkust, defaults={'latitude': 22.33584, 'longitude': 114.26355})

        Campus.objects.get_or_create(name='Main Campus', university=cuhk, defaults={'latitude': 22.41907, 'longitude': 114.20693})