from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from core.models import Accommodation, University, Member, Specialist, Reservation, Campus, Owner

class CampusAPITest(APITestCase):
    def setUp(self):
        """Set up test data for the tests"""
        # Create a test university
        self.university = University.objects.create(
            name="Test University",
            country="Test Country"
        )
        
        # Create a test campus
        self.campus = Campus.objects.create(
            name="Test Campus",
            latitude=22.2830,
            longitude=114.1371,
            university=self.university
        )

        self.client = APIClient()
    
    def test_get_campus_list(self):
        """Test retrieving a list of campuses"""
        # Use Django's reverse function with the router pattern name
        url = '/api/campuses/'  # Based on DefaultRouter naming convention
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_campus_detail(self):
        """Test retrieving a specific campus"""
        # Use Django's reverse function with the router pattern name
        url = f'/api/campuses/{self.campus.id}/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AccommodationAPITest(APITestCase):
    def setUp(self):
        """Set up test data for the tests"""
        # Import datetime for dynamic dates
        from datetime import datetime, timedelta
        
        # Calculate dates relative to today
        today = datetime.now().date()
        start_date = today - timedelta(days=30)  # 30 days ago
        end_date = today + timedelta(days=180)   # 180 days in the future

        # Create a test owner
        self.owner = Owner.objects.create(
            name="Test Owner",
            email="owner@example.com",
            phone="12345678"
        )
        
        # Create a test university
        self.university = University.objects.create(
            name="Test University",
            country="Test Country"
        )
        
        # Create a test accommodation
        self.accommodation = Accommodation.objects.create(
            name="Test Accommodation",
            building_name="Main Campus",
            description="Test Description",
            type="APARTMENT",
            num_bedrooms=2,
            num_beds=2,
            address="Test Address",
            geo_address="12345678901234567",
            latitude=22.28405,  # Main Campus coordinates
            longitude=114.13784,  # Main Campus coordinates
            available_from=start_date,
            available_to=end_date,
            monthly_rent=5000,
            owner=self.owner
        )
        
        # Associate accommodation with university
        self.accommodation.universities.add(self.university)
    
    def test_get_accommodation_list(self):
        """Test retrieving a list of accommodations"""
        url = '/api/accommodations/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_accommodation_detail(self):
        """Test retrieving a specific accommodation"""
        url = f'/api/accommodations/{self.accommodation.id}/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_accommodation(self):
        """Test creating a new accommodation"""
        url = '/api/accommodations/'
        data = {
            'name': 'New Accommodation',
            'building_name': 'Main Campus',
            'description': 'New Description',
            'type': 'APARTMENT',
            'num_bedrooms': 3,
            'num_beds': 4,
            'address': 'New Address',
            'geo_address': '12345678901234567',
            'latitude': 22.28405,
            'longitude': 114.13784,
            'available_from': '2023-02-01',
            'available_to': '2023-11-30',
            'monthly_rent': '6000.00',
            
            'owner_details': {
                'name': self.owner.name,
                'email': self.owner.email,
                'phone': self.owner.phone
            },

            'university_ids': [self.university.id]
        }
        response = self.client.post(url, data, format='json')
        print(f"Response content: {response.content.decode()}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class ReservationAPITest(APITestCase):
    def setUp(self):
        """Set up test data for the tests"""

        # Import datetime for dynamic dates
        from datetime import datetime, timedelta
        
        # Calculate dates relative to today
        today = datetime.now().date()
        start_date = today - timedelta(days=30)  # 30 days ago
        end_date = today + timedelta(days=180)   # 180 days in the future

        # Create a test owner
        self.owner = Owner.objects.create(
            name="Test Owner",
            email="owner@example.com",
            phone="12345678"
        )
        
        # Create a test university
        self.university = University.objects.create(
            name="Test University",
            country="Test Country"
        )
        
        # Create a test member
        self.member = Member.objects.create(
            name="Test Member",
            email="member@example.com",
            phone="12345678",
            university=self.university
        )
        
        # Create a test accommodation
        self.accommodation = Accommodation.objects.create(
            name="Test Accommodation",
            building_name="Main Campus",
            description="Test Description",
            type="APARTMENT",
            num_bedrooms=2,
            num_beds=2,
            address="Test Address",
            geo_address="12345678901234567",  # Add a valid geo_address
            latitude=22.28405,  # Main Campus coordinates
            longitude=114.13784,  # Main Campus coordinates
            available_from=start_date,
            available_to=end_date,
            monthly_rent=5000,
            owner=self.owner,
            is_available=True
        )
        
        # Associate accommodation with university
        self.accommodation.universities.add(self.university)
        
        # Create a reservation
        self.reservation = Reservation.objects.create(
            accommodation=self.accommodation,
            member=self.member,
            reserved_from="2023-06-01",
            reserved_to="2023-07-31",
            contact_name="Test Contact",
            contact_phone="12345678",
            status="PENDING"
        )
    
    def test_create_reservation(self):
        """Test creating a reservation"""
        from datetime import datetime, timedelta
    
        # Use dates within the accommodation's availability period
        today = datetime.now().date()
        reserve_from = today + timedelta(days=10)
        reserve_to = today + timedelta(days=20)
        
        url = '/api/reservations/'
        data = {
            'accommodation': self.accommodation.id,
            'member': self.member.id,
            'reserved_from': reserve_from.strftime('%Y-%m-%d'),  # Use future date
            'reserved_to':  reserve_to.strftime('%Y-%m-%d'),      # Use future date
            'contact_name': 'New Contact',
            'contact_phone': '87654321'
        }
        response = self.client.post(url, data, format='json')
        print(f"Response content: {response.content.decode()}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_cancel_reservation(self):
        """Test cancelling a reservation"""
        url = f'/api/reservations/{self.reservation.id}/cancel/'  # Make sure this matches your URL configuration
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)