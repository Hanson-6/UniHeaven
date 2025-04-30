from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from core.models import Accommodation, University, Member, Specialist, Reservation, Campus, Owner, Rating, ActionLog
from core.views import AccommodationViewSet, CampusViewSet, ReservationViewSet, MemberViewSet, RatingViewSet

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

    def test_search_accommodations(self):
        """Test searching for accommodations with filters"""
        # First, create a member for the search
        member = Member.objects.create(
            name="Search Test Member",
            email="search_test@example.com",
            phone="87654321",
            university=self.university
        )
        
        # Create a campus for distance-based search
        campus = Campus.objects.create(
            name="Test Search Campus",
            latitude=22.2830,
            longitude=114.1371,
            university=self.university
        )
        
        # Search endpoint with parameters
        url = '/api/accommodations/search/'
        params = {
            'member_id': member.id,
            'type': 'APARTMENT',
            'num_beds': 2,
            'min_price': 4000,
            'max_price': 6000,
            'campus_id': campus.id,
            'sort_by': 'distance'
        }
        response = self.client.get(url, params, format='json')
        print(f"Search response content: {response.content.decode()}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_accommodation_unavailable(self):
        """Test marking an accommodation as unavailable"""
        # Ensure accommodation is available
        self.accommodation.is_available = True
        self.accommodation.save()
        
        # Create a specialist for the action
        specialist = Specialist.objects.create(
            name="Test Specialist",
            email="specialist@example.com",
            university=self.university
        )
        
        url = f'/api/accommodations/{self.accommodation.id}/mark_unavailable/'
        data = {'specialist_id': specialist.id}
        response = self.client.post(url, data, format='json')
        print(f"Mark unavailable response: {response.content.decode()}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh accommodation from database and check availability
        self.accommodation.refresh_from_db()
        self.assertFalse(self.accommodation.is_available)    

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

class MemberAPITest(APITestCase):
    def setUp(self):
        """Set up test data for the tests"""
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
        
        # Create a test owner
        self.owner = Owner.objects.create(
            name="Test Owner",
            email="owner@example.com",
            phone="12345678"
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
            latitude=22.28405,
            longitude=114.13784,
            available_from="2023-01-01",
            available_to="2023-12-31",
            monthly_rent=5000,
            owner=self.owner,
            is_available=True
        )
        
        # Associate accommodation with university
        self.accommodation.universities.add(self.university)
        
        # Create a reservation for the member
        self.reservation = Reservation.objects.create(
            accommodation=self.accommodation,
            member=self.member,
            reserved_from="2023-06-01",
            reserved_to="2023-07-31",
            contact_name="Test Contact",
            contact_phone="12345678",
            status="PENDING"
        )
        
        self.client = APIClient()
    
    def test_get_member_reservations(self):
        """Test retrieving a member's reservations"""
        url = f'/api/members/{self.member.id}/reservations/'
        response = self.client.get(url, format='json')
        print(f"Member reservations response: {response.content.decode()}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the response contains at least one reservation
        self.assertGreater(len(response.data), 0)

class RatingAPITest(APITestCase):
    def setUp(self):
        """Set up test data for the tests"""
        # Create a test university
        self.university = University.objects.create(
            name="Test University",
            country="Test Country"
        )
        
        # Create a test owner
        self.owner = Owner.objects.create(
            name="Test Owner",
            email="owner@example.com",
            phone="12345678"
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
            latitude=22.28405,
            longitude=114.13784,
            available_from="2023-01-01",
            available_to="2023-12-31",
            monthly_rent=5000,
            owner=self.owner,
            is_available=True
        )
        
        # Associate accommodation with university
        self.accommodation.universities.add(self.university)
        
        # Create a test member
        self.member = Member.objects.create(
            name="Test Member",
            email="member@example.com",
            phone="12345678",
            university=self.university
        )
        
        # Create a test specialist
        self.specialist = Specialist.objects.create(
            name="Test Specialist",
            email="specialist@example.com",
            university=self.university
        )
        
        # Create a completed reservation
        self.reservation = Reservation.objects.create(
            accommodation=self.accommodation,
            member=self.member,
            reserved_from="2023-01-01",
            reserved_to="2023-01-10",
            contact_name="Test Contact",
            contact_phone="12345678",
            status="COMPLETED"
        )
        
        # Create a rating
        self.rating = Rating.objects.create(
            accommodation=self.accommodation,
            member=self.member,
            reservation=self.reservation,
            score=4,
            comment="Good accommodation",
            is_approved=False,
            moderated_by=None
        )
        
        self.client = APIClient()
    
    def test_moderate_rating(self):
        """Test moderating a rating"""
        url = f'/api/ratings/{self.rating.id}/moderate/'
        data = {
            'specialist_id': self.specialist.id,
            'is_approved': True,
            'moderation_note': 'Approved after review'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh rating from database and check moderation
        self.rating.refresh_from_db()
        self.assertTrue(self.rating.is_approved)
        self.assertEqual(self.rating.moderated_by.id, self.specialist.id)  # Compare IDs instead of objects
        self.assertEqual(self.rating.moderation_note, 'Approved after review')
    
    def test_get_pending_ratings(self):
        """Test retrieving pending ratings"""
        url = '/api/ratings/pending/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that response is paginated and has results
        self.assertIn('count', response.data)
        self.assertGreater(response.data['count'], 0)

class ActionLogAPITest(APITestCase):
    def setUp(self):
        """Set up test data for the tests"""
        # Create a test university
        self.university = University.objects.create(
            name="Test University",
            country="Test Country"
        )
        
        # Create a test owner
        self.owner = Owner.objects.create(
            name="Test Owner",
            email="owner@example.com",
            phone="12345678"
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
            latitude=22.28405,
            longitude=114.13784,
            available_from="2023-01-01",
            available_to="2023-12-31",
            monthly_rent=5000,
            owner=self.owner,
            is_available=True
        )
        
        # Create action logs
        self.action_log1 = ActionLog.objects.create(
            action_type="CREATE_ACCOMMODATION",
            user_type="SPECIALIST",
            user_id=1,
            accommodation_id=self.accommodation.id,
            details="Created accommodation 'Test Accommodation'"
        )
        
        self.action_log2 = ActionLog.objects.create(
            action_type="UPDATE_ACCOMMODATION",
            user_type="SPECIALIST",
            user_id=1,
            accommodation_id=self.accommodation.id,
            details="Updated accommodation 'Test Accommodation'"
        )
        
        self.client = APIClient()
    
    def test_get_action_logs(self):
        """Test retrieving action logs with filters"""
        url = '/api/action-logs/'
        params = {
            'action_type': 'CREATE_ACCOMMODATION',
            'user_type': 'SPECIALIST'
        }
        response = self.client.get(url, params, format='json')
        print(f"Action logs response: {response.content.decode()}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test without filters
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class APIRequestFactoryTest(APITestCase):
    def setUp(self):
        """Set up test data for the tests"""
        # Create a test university
        self.university = University.objects.create(
            name="Test University",
            country="Test Country"
        )
        
        # Create a test owner
        self.owner = Owner.objects.create(
            name="Test Owner",
            email="owner@example.com",
            phone="12345678"
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
            latitude=22.28405,
            longitude=114.13784,
            available_from="2023-01-01",
            available_to="2023-12-31",
            monthly_rent=5000,
            owner=self.owner,
            is_available=True
        )
        
        # Associate accommodation with university
        self.accommodation.universities.add(self.university)
        
        self.factory = APIRequestFactory()
    
    def test_accommodation_list_direct(self):
        """Test accommodation list view directly with APIRequestFactory"""
        view = AccommodationViewSet.as_view({'get': 'list'})
        request = self.factory.get('/api/accommodations/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_accommodation_detail_direct(self):
        """Test accommodation detail view directly with APIRequestFactory"""
        view = AccommodationViewSet.as_view({'get': 'retrieve'})
        request = self.factory.get(f'/api/accommodations/{self.accommodation.id}/')
        response = view(request, pk=self.accommodation.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Accommodation')

class MultiUniversityTest(APITestCase):
    def setUp(self):
        """Set up test data for multi-university tests"""
        # Create test universities
        self.university1 = University.objects.create(
            name="HKU Test",
            country="China Hong Kong"
        )
        
        self.university2 = University.objects.create(
            name="HKUST Test",
            country="China Hong Kong"
        )
        
        # Create test members for each university
        self.member1 = Member.objects.create(
            name="HKU Member",
            email="hku_member@example.com",
            university=self.university1
        )
        
        self.member2 = Member.objects.create(
            name="HKUST Member",
            email="hkust_member@example.com",
            university=self.university2
        )
        
        # Create a test owner
        self.owner = Owner.objects.create(
            name="Test Owner",
            email="owner@example.com",
            phone="12345678"
        )
        
        # Create a test accommodation shared between universities
        self.accommodation = Accommodation.objects.create(
            name="Shared Accommodation",
            building_name="Central Building",
            description="Available to both universities",
            type="APARTMENT",
            num_bedrooms=2,
            num_beds=2,
            address="Shared Address",
            geo_address="12345678901234567",
            latitude=22.28000,
            longitude=114.15000,
            available_from="2023-01-01",
            available_to="2023-12-31",
            monthly_rent=5000,
            owner=self.owner,
            is_available=True
        )
        
        # Associate accommodation with both universities
        self.accommodation.universities.add(self.university1)
        self.accommodation.universities.add(self.university2)
        
        self.client = APIClient()
    
    def test_accommodation_multiple_universities(self):
        """Test that an accommodation can be associated with multiple universities"""
        # Check that accommodation is associated with both universities
        universities = self.accommodation.universities.all()
        self.assertEqual(universities.count(), 2)
        self.assertIn(self.university1, universities)
        self.assertIn(self.university2, universities)
        
        # Test search from each university's perspective
        # University 1 member should see the accommodation
        url = '/api/accommodations/search/'
        params = {'member_id': self.member1.id}
        response = self.client.get(url, params, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
        # University 2 member should also see the accommodation
        params = {'member_id': self.member2.id}
        response = self.client.get(url, params, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)