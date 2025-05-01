from rest_framework import serializers
from django.utils import timezone
from .models import (
    Accommodation, Member, Specialist,
    Reservation, Rating, Campus, Owner, ActionLog, University, AccommodationUniversity
)

# -------------------- Owner --------------------
class OwnerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if self.context.get('allow_existing_email', False):
            try:
                Owner.objects.get(email=value)
                return value
            except Owner.DoesNotExist:
                pass
        else:
            if Owner.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already in use.")
        return value

    class Meta:
        model = Owner
        fields = ['name', 'email', 'phone', 'address']

# -------------------- University --------------------
class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['name', 'country', 'address']

# -------------------- Campus --------------------
class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ['name', 'latitude', 'longitude', 'university']

# -------------------- Member --------------------
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'name', 'email', 'phone', 'university']

# -------------------- Specialist --------------------
class CEDARSSpecialistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialist
        fields = ['id', 'name', 'email', 'phone', 'university']

# -------------------- ActionLog --------------------
class ActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionLog
        fields = '__all__'

# -------------------- Accommodation --------------------
class AccommodationSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    owner_details = OwnerSerializer(write_only=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    universities = UniversitySerializer(many=True, read_only=True)
    university_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=University.objects.all(),
        write_only=True
    )

    class Meta:
        model = Accommodation
        fields = [
            'id', 'name', 'building_name', 'room_number', 'flat_number', 'floor_number',
            'description', 'type', 'type_display',
            'num_bedrooms', 'num_beds', 'address', 'geo_address',
            'latitude', 'longitude', 'available_from', 'available_to',
            'monthly_rent', 'owner', 'owner_details', 'is_available', 
            'photo', 'average_rating', 'rating_count', 'universities', 'university_ids',
        ]

    def create(self, validated_data):
        owner_data = validated_data.pop('owner_details', None)
        university_ids = validated_data.pop('university_ids', [])
        if owner_data:
            email = owner_data.get('email')
            try:
                owner = Owner.objects.get(email=email)
            except Owner.DoesNotExist:
                owner = Owner.objects.create(**owner_data)
            validated_data['owner'] = owner
        accommodation = Accommodation.objects.create(**validated_data)
        accommodation.universities.set(university_ids)
        return accommodation

    def update(self, instance, validated_data):
        owner_data = validated_data.pop('owner_details', None)
        university_ids = validated_data.pop('university_ids', [])
        if owner_data:
            owner, created = Owner.objects.get_or_create(
                email=owner_data['email'],
                defaults={
                    'name': owner_data['name'],
                    'phone': owner_data.get('phone', ''),
                    'address': owner_data.get('address', '')
                }
            )
            validated_data['owner'] = owner
        instance = super().update(instance, validated_data)
        instance.universities.set(university_ids)
        return instance

    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if ratings.exists():
            try:
                avg = sum(rating.score for rating in ratings) / ratings.count()
                return round(avg, 1)
            except Exception as e:
                return None
        return None
        
    def get_rating_count(self, obj):
        return obj.ratings.count()

# -------------------- Reservation --------------------
class ReservationSerializer(serializers.ModelSerializer):
    accommodation_name = serializers.ReadOnlyField(source='accommodation.name')
    member_name = serializers.ReadOnlyField(source='member.name')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_be_rated = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'accommodation', 'accommodation_name', 'member', 'member_name',
            'reserved_from', 'reserved_to', 'status', 'status_display', 
            'can_be_rated', 'can_be_cancelled', 'created_at', 'updated_at'
        ]

    def get_can_be_rated(self, obj):
        return obj.can_be_rated()
        
    def get_can_be_cancelled(self, obj):
        return obj.can_be_cancelled()
    
    def validate(self, data):
        reserved_from = data.get('reserved_from')
        reserved_to = data.get('reserved_to')
        accommodation = data.get('accommodation')
        
        if reserved_from and reserved_to and accommodation:
            # Check if end date is after start date
            if reserved_from > reserved_to:
                raise serializers.ValidationError("End date must be after start date")
            
            # Prevent reservations starting in the past (for new reservations)
            if self.instance is None and reserved_from < timezone.now().date():
                raise serializers.ValidationError("Reservation start date cannot be in the past")
            
            # Ensure requested dates are within accommodation's availability
            if reserved_from < accommodation.available_from or reserved_to > accommodation.available_to:
                raise serializers.ValidationError(
                    "Requested dates are outside the accommodation's availability period"
                )
            
            # Check for overlapping reservations
            overlapping_reservations = Reservation.objects.filter(
                accommodation=accommodation,
                status__in=['PENDING', 'CONFIRMED'],
                reserved_from__lt=reserved_to,
                reserved_to__gt=reserved_from
            ).exclude(id=self.instance.id if self.instance else None)
            
            if overlapping_reservations.exists():
                raise serializers.ValidationError(
                    "The accommodation is already reserved for the selected dates"
                )
        
        return data

# -------------------- Rating --------------------
class RatingSerializer(serializers.ModelSerializer):
    member_name = serializers.ReadOnlyField(source='member.name')

    class Meta:
        model = Rating
        fields = [
            'id', 'accommodation', 'member', 'member_name', 'reservation',
            'score', 'comment', 'created_at'
        ]

    def validate(self, data):
        reservation = data.get('reservation')
        if reservation:
            if reservation.status != 'COMPLETED':
                raise serializers.ValidationError("Can only rate completed reservations")

            if not reservation.can_be_rated():
                raise serializers.ValidationError("This reservation has already been rated")
        else:
            raise serializers.ValidationError("Reservation is required for rating.")
        return data

# -------------------- AccommodationUniversity --------------------
class AccommodationUniversitySerializer(serializers.ModelSerializer):
    accommodation_name = serializers.CharField(source='accommodation.name')
    university_name = serializers.CharField(source='university.name')

    class Meta:
        model = AccommodationUniversity
        fields = ['accommodation_name', 'university_name']