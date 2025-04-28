from django.test import TestCase
from core.models import Accommodation, Campus, University, Owner, Rating, Reservation, Member, Specialist, ActionLog, AccommodationUniversity
import math
from datetime import date, timedelta

# Canonical buildings → (lat, long)
BUILDINGS = {
    "Main Campus":                   (22.28405, 114.13784),
    "Sassoon Road Campus":           (22.26750, 114.12881),
    "Swire Institute of Marine Science": (22.20805, 114.26021),
    "Kadoorie Centre":               (22.43022, 114.11429),
    "Faculty of Dentistry":          (22.28649, 114.14426),
}

def future(n_days):
    """Return a date n_days ahead of today as YYYY-MM-DD."""
    return (date.today() + timedelta(days=n_days)).isoformat()


class DistanceCalculationTest(TestCase):
    def setUp(self):
        """Set up test data for distance calculation tests"""
        # Create a test owner
        self.owner = Owner.objects.create(
            name="Test Owner", 
            email="distance_test@example.com",
            phone="1234567890"
        )
        
        # Create a test university
        self.university = University.objects.create(
            name="Test University",
            country="Test Country"
        )
        
        # Create test accommodation using HKU coordinates
        lat, lon = BUILDINGS["Main Campus"]
        self.accommodation_hku = Accommodation.objects.create(
            name="HKU Accommodation",
            building_name="Main Campus",
            description="Near HKU",
            type="APARTMENT",
            num_bedrooms=2,
            num_beds=2,
            address="HKU Area",
            geo_address="HKU12345678901234",
            latitude=lat,  # Main Campus coordinates
            longitude=lon,
            available_from=future(1),
            available_to=future(356),
            monthly_rent=5000,
            owner=self.owner,
            is_available=True
        )
        self.accommodation_hku.universities.add(self.university)

        lat, lon = BUILDINGS["Sassoon Road Campus"]
        self.accommodation = Accommodation.objects.create(
            name="A1",
            building_name="Sassoon Road Campus",
            description="d",
            type="APARTMENT",
            num_bedrooms=1,
            num_beds=1,
            address="Addr",
            geo_address="12345678901234567",
            latitude=lat,
            longitude=lon,
            available_from=future(10),
            available_to=future(400),
            monthly_rent=1000,
            owner=self.owner,
        ) 
        
        # Create test campuses
        self.campus_hku = Campus.objects.create(
            name="HKU Main Campus",
            latitude=22.28405,
            longitude=114.13784,
            university=self.university
        )
        
        self.campus_hkust = Campus.objects.create(
            name="HKUST Campus",
            latitude=22.33584,
            longitude=114.26355,
            university=self.university
        )
    
    def test_calculate_distance_same_location(self):
        """Test distance calculation for same location (should be 0)"""
        distance = self.accommodation_hku.calculate_distance(self.campus_hku)
        self.assertAlmostEqual(distance, 0, delta=0.01)
    
    def test_calculate_distance_different_location(self):
        """Test distance calculation for different locations"""
        distance = self.accommodation_hku.calculate_distance(self.campus_hkust)
        # The actual value depends on your implementation
        self.assertGreater(distance, 0)
        # Let's assume it should be around 14-15 km between HKU and HKUST
        self.assertAlmostEqual(distance, 14.5, delta=1.0)
    
    def test_distance_calculation_components(self):
        """Test the individual components of the distance calculation"""
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert latitude and longitude from degrees to radians
        lat1 = math.radians(self.accommodation_hku.latitude)
        lon1 = math.radians(self.accommodation_hku.longitude)
        lat2 = math.radians(self.campus_hkust.latitude)
        lon2 = math.radians(self.campus_hkust.longitude)
        
        # Equirectangular approximation
        x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
        y = (lat2 - lat1)
        expected_distance = R * math.sqrt(x*x + y*y)
        
        # Compare with the method's result
        actual_distance = self.accommodation_hku.calculate_distance(self.campus_hkust)
        self.assertAlmostEqual(actual_distance, expected_distance, delta=0.0001)

    def test_average_rating_and_count(self):
        """Test the average_rating and rating_count methods"""
        # Create a rating for the accommodation
        Rating.objects.create(
            accommodation=self.accommodation_hku,
            member=Member.objects.create(
                name="Test Member",
                email="rating_test@example.com",
                university=self.university
            ),
            reservation=Reservation.objects.create(
                accommodation=self.accommodation_hku,
                member=Member.objects.get(email="rating_test@example.com"),
                reserved_from="2023-01-01",
                reserved_to="2023-01-10",
                contact_name="Test Contact",
                contact_phone="1234567890",
                status="COMPLETED"
            ),
            score=4,
            comment="Good accommodation"
        )
        
        # Test the methods
        self.assertEqual(self.accommodation_hku.rating_count(), 1)
        self.assertEqual(self.accommodation_hku.average_rating(), 4)

    def test_reservation_methods(self):
        """Test methods on the Reservation model"""
        from datetime import datetime, timedelta
        
        # Create a test member
        member = Member.objects.create(
            name="Reservation Test Member",
            email="reservation_test@example.com",
            university=self.university
        )
        
        # Create a pending reservation
        pending_reservation = Reservation.objects.create(
            accommodation=self.accommodation_hku,
            member=member,
            reserved_from=datetime.now().date() + timedelta(days=10),
            reserved_to=datetime.now().date() + timedelta(days=20),
            contact_name="Test Contact",
            contact_phone="1234567890",
            status="PENDING"
        )
        
        # Test can_be_cancelled method
        self.assertTrue(pending_reservation.can_be_cancelled())
        
        # Test cancel method
        original_is_available = self.accommodation_hku.is_available
        self.accommodation_hku.is_available = False
        self.accommodation_hku.save()
        
        pending_reservation.cancel()
        pending_reservation.refresh_from_db()
        self.accommodation_hku.refresh_from_db()
        
        self.assertEqual(pending_reservation.status, "CANCELLED")
        self.assertTrue(self.accommodation_hku.is_available)
        
        # Test completed reservation
        completed_reservation = Reservation.objects.create(
            accommodation=self.accommodation_hku,
            member=member,
            reserved_from=datetime.now().date() - timedelta(days=20),
            reserved_to=datetime.now().date() - timedelta(days=10),
            contact_name="Test Contact",
            contact_phone="1234567890",
            status="COMPLETED"
        )
        
        # Test can_be_rated method
        self.assertTrue(completed_reservation.can_be_rated())

    def test_model_string_representations(self):
        """Test the string representation of models"""
        # Owner string representation
        owner = Owner.objects.create(
            name="String Test Owner",
            email="string_test@example.com",
            phone="9876543210"
        )
        self.assertEqual(str(owner), "String Test Owner")
        
        # Member string representation
        member = Member.objects.create(
            name="String Test Member",
            email="string_member@example.com",
            university=self.university
        )
        self.assertEqual(str(member), "String Test Member")
        
        # Specialist string representation
        specialist = Specialist.objects.create(
            name="String Test Specialist",
            email="string_specialist@example.com",
            university=self.university
        )
        self.assertEqual(str(specialist), "String Test Specialist")
        
        # Other models string representation
        self.assertTrue(str(self.campus_hku))
        self.assertTrue(str(self.accommodation_hku))

    def test_accommodation_universities_relation(self):
        """Test the relationship between Accommodation and University"""
        # Test that the accommodation is correctly associated with universities
        universities = self.accommodation_hku.universities.all()
        self.assertEqual(universities.count(), 1)
        self.assertEqual(universities.first(), self.university)
        
        # Test adding another university
        new_university = University.objects.create(
            name="Another University",
            country="Test Country"
        )
        self.accommodation_hku.universities.add(new_university)
        self.assertEqual(self.accommodation_hku.universities.count(), 2)

    def test_action_log(self):
        """Test the ActionLog model"""
        log = ActionLog.objects.create(
            action_type="Create Reservation",
            user_type="MEMBER",
            user_id=1,
            accommodation_id=self.accommodation_hku.id,
            details="Test log entry"
        )
        self.assertTrue(str(log))
        
        # Test logs ordering
        ActionLog.objects.create(
            action_type="Create Accommodation",
            user_type="SPECIALIST",
            user_id=2,
            accommodation_id=self.accommodation_hku.id,
            details="Another test log entry"
        )
        
        logs = ActionLog.objects.all()
        self.assertEqual(logs.count(), 2)
        # Check that the newest log is first (if ordered by '-created_at')
        self.assertEqual(logs.first().action_type, "Create Accommodation")

    def test_university_str_extra(self):
        """Covers models.py line 48"""
        self.assertEqual(str(self.university), "Test University")

    def test_accommodation_university_str_extra(self):
        """Covers models.py line 140"""
        link = AccommodationUniversity.objects.get(
            accommodation=self.accommodation_hku,
            university=self.university
        )
        expected = f"{self.accommodation_hku.name} - {self.university.name}"
        self.assertEqual(str(link), expected)

    def test_average_rating_none(self):
        """Covers models.py line 222"""
        self.assertIsNone(self.accommodation_hku.average_rating())
        self.assertEqual(self.accommodation_hku.rating_count(), 0)

    def test_cancel_not_allowed(self):
        """Covers models.py lines 285-293 (else-branch)"""
        member = Member.objects.create(
            name="NoCancel",
            email="nocancel@example.com",
            university=self.university
        )
        confirmed = Reservation.objects.create(
            accommodation=self.accommodation_hku,
            member=member,
            reserved_from=date.today() + timedelta(days=5),  
            reserved_to=date.today() + timedelta(days=15), 
            contact_name="X",
            contact_phone="Y",
            status="CONFIRMED"
        )
        old_status = confirmed.status
        old_available = self.accommodation_hku.is_available
        confirmed.cancel()   # cannot cancel → else branch
        confirmed.refresh_from_db()
        self.accommodation_hku.refresh_from_db()
        self.assertEqual(confirmed.status, old_status)
        self.assertEqual(self.accommodation_hku.is_available, old_available)

    def test_reservation_and_rating_str_extra(self):
        """Covers models.py lines 296-297 & 346"""
        member = Member.objects.create(
            name="StrMember",
            email="strmember@example.com",
            university=self.university
        )
        res = Reservation.objects.create(
            accommodation=self.accommodation_hku,
            member=member,
            reserved_from=date.today() + timedelta(days=20),  # future
            reserved_to=date.today() + timedelta(days=30),
            contact_name="C",
            contact_phone="P",
            status="COMPLETED"
        )
        self.assertIn("reservation of", str(res))

        rating = Rating.objects.create(
            accommodation=self.accommodation_hku,
            member=member,
            reservation=res,
            score=5
        )
        self.assertIn("5-star rating", str(rating))
