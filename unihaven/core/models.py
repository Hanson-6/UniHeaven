from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import math

class Owner(models.Model):
    """
    Property owner who offers accommodations for rent

    Primary Key:
        - email: Unique email address for the owner
            - Reason: the email itself is unique when created
            - Used: to identify the owner in the system
    """
    
    name = models.CharField(max_length=200, blank=False, null=False)
    email = models.EmailField(primary_key=True, unique=True)
    phone = models.CharField(max_length=20, blank=True)  # 添加 blank=True
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Owner"
        verbose_name_plural = "Owners"

    def __str__(self):
        return self.name

class University(models.Model):
    """
    University that owns the campus

    Primary Key:
        - (country, name): The combination of country and university name for the university
    """
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=False)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('country', 'name')
        verbose_name = "University"
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name

class Campus(models.Model):
    """
    Campus or premises of HKU for distance calculation
    
    Primary Key:
        - (name, university_name): The combination of campus name and university name for the campus
    """
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    university = models.ForeignKey(
        University,
        related_name='campuses',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('university', 'name')
        verbose_name = "Campus"
        verbose_name_plural = "Campuses"

    def __str__(self):
        return f"{self.name}"

class Member(models.Model):
    """Member of HKU who can search and reserve accommodations"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, unique=True)
    university = models.ForeignKey(
        University,
        related_name='members',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Member"
        verbose_name_plural = "Members"

    def __str__(self):
        return self.name

class Specialist(models.Model):
    """
    Specialist who manages accommodations and reservations
    """
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    university = models.ForeignKey(
        University,
        related_name='specialists',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Specialist"
        verbose_name_plural = "Specialists"

    def __str__(self):
        return self.name

class AccommodationUniversity(models.Model):
    """
    Intermediate table to manage the many-to-many relationship between Accommodation and University
    """
    accommodation = models.ForeignKey(
        'Accommodation',
        on_delete=models.CASCADE,
        related_name='university_mappings'
    )
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='accommodation_mappings'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('accommodation', 'university')
        verbose_name = "Relation between Accommodation and University"
        verbose_name_plural = "Relations between Accommodation and University"

    def __str__(self):
        return f"{self.accommodation.name} - {self.university.name}"

class Accommodation(models.Model):
    """
    Accommodation that can be rented by HKU members
    """
    # Basic info
    name = models.CharField(max_length=200)
    building_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to='photos',
        blank=True,
        null=True
    )

    room_number = models.CharField(max_length=20, blank=True)
    flat_number = models.CharField(max_length=20, blank=True)
    floor_number = models.CharField(max_length=20, blank=True)

    # Many-to-many relationship with University
    universities = models.ManyToManyField(
        University,
        through='AccommodationUniversity',
        related_name='accommodations'
    )

    # value and display info
    TYPE_CHOICES = [
        ('APARTMENT', 'Apartment'),
        ('HOUSE', 'House'),
        ('SHARED', 'Shared Room'),
        ('STUDIO', 'Studio'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    num_bedrooms = models.PositiveIntegerField()
    num_beds = models.PositiveIntegerField()

    # Location data
    address = models.TextField()
    geo_address = models.CharField(max_length=19)
    latitude = models.FloatField()
    longitude = models.FloatField()

    # Availability and cost
    available_from = models.DateField()
    available_to = models.DateField()
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)

    # Owner info
    owner = models.ForeignKey(
        Owner,
        related_name='accommodations',
        on_delete=models.CASCADE,
        to_field='email'
    )

    # Status tracking
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_distance(self, campus: Campus):
        """
        Calculate distance to campus in kilometers using equirectangular projection
        """
        # Earth radius in kilometers
        R = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        lat2 = math.radians(campus.latitude)
        lon2 = math.radians(campus.longitude)

        # Equirectangular approximation
        x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
        y = (lat2 - lat1)
        d = R * math.sqrt(x*x + y*y)

        return d

    def average_rating(self):
        """Calculate the average rating for this accommodation"""
        ratings = self.ratings.all()
        if not ratings:
            return None
        return sum(rating.score for rating in ratings) / len(ratings)

    def rating_count(self):
        """Get the number of ratings for this accommodation"""
        return self.ratings.count()

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Accommodation"
        verbose_name_plural = "Accommodations"

        unique_together = (
            
        )

class Reservation(models.Model):
    """
    Reservation of accommodation by an HKU member
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.CASCADE
    )

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE
    )

    reserved_from = models.DateField()
    reserved_to = models.DateField()
    
    # New contact fields
    contact_name = models.CharField(max_length=200)
    contact_phone = models.CharField(max_length=20)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_be_rated(self):
        """
        Check if this reservation can be rated
        """
        return self.status == 'COMPLETED' and not hasattr(self, 'rating')

    def can_be_cancelled(self):
        """
        Check if this reservation can be cancelled
        """
        return self.status == 'PENDING'

    def cancel(self):
        """
        Cancel this reservation and handle side effects
        """
        if self.can_be_cancelled():
            self.status = 'CANCELLED'
            self.save()
            
            # Make accommodation available again
            self.accommodation.is_available = True
            self.accommodation.save()
            
        return False

    def __str__(self):
        info = f"{self.member.name}'s reservation of {self.accommodation.name}"
        return info
    

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"

class Rating(models.Model):
    """
    Rating given by an HKU member for an accommodation after stay
    """
    accommodation = models.ForeignKey(
        Accommodation,
        related_name='ratings',
        on_delete=models.CASCADE
    )

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE
    )

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE
    )

    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Moderation fields
    is_approved = models.BooleanField(default=True)
    moderated_by = models.ForeignKey(
        Specialist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    moderation_date = models.DateTimeField(null=True, blank=True)
    moderation_note = models.TextField(blank=True)

    class Meta:
        unique_together = ('accommodation', 'member', 'reservation')
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"

    def __str__(self):
        return f"{self.member.name}'s {self.score}-star rating for {self.accommodation.name}"

class ActionLog(models.Model):
    """
    Log of actions performed in the system for audit purposes
    """
    ACTION_TYPES = [
        ('CREATE_ACCOMMODATION', 'Create Accommodation'),
        ('UPDATE_ACCOMMODATION', 'Update Accommodation'),
        ('DELETE_ACCOMMODATION', 'Delete Accommodation'),
        ('MARK_UNAVAILABLE', 'Mark Unavailable'),
        ('CREATE_RESERVATION', 'Create Reservation'),
        ('UPDATE_RESERVATION', 'Update Reservation'),
        ('CANCEL_RESERVATION', 'Cancel Reservation'),
        ('CREATE_RATING', 'Create Rating'),
        ('MODERATE_RATING', 'Moderate Rating'),
        ('UPLOAD_PHOTO', 'Upload Photo'),
        ('DELETE_PHOTO', 'Delete Photo'),
    ]
    
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    user_type = models.CharField(max_length=20, default='SPECIALIST')
    user_id = models.PositiveIntegerField(null=True, blank=True)
    accommodation_id = models.PositiveIntegerField(null=True, blank=True)
    reservation_id = models.PositiveIntegerField(null=True, blank=True)
    rating_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at', 'id']
        verbose_name = "Action Log"
        verbose_name_plural = "Action Logs"
    
    def __str__(self):
        return f"{self.action_type} at {self.created_at}"