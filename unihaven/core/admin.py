from django.contrib import admin
from .models import (
    Accommodation, Member, Specialist,
    Reservation, Rating, Campus, Owner, University, AccommodationUniversity
)

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')
    search_fields = ('name', 'email')


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'address', 'created_at')
    search_fields = ('name', 'country')


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'university')

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'university')
    search_fields = ('name', 'email', 'university__name')


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'university')
    search_fields = ('name', 'email', 'university')


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'num_bedrooms', 'num_beds', 'monthly_rent', 'is_available')
    list_filter = ('type', 'is_available', 'num_bedrooms')
    search_fields = ('name', 'building_name', 'address')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('accommodation', 'member', 'reserved_from', 'reserved_to', 'status')
    list_filter = ('status',)
    search_fields = ('accommodation__name', 'member__name')
    

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('accommodation', 'member', 'score', 'created_at')
    list_filter = ('score',)


@admin.register(AccommodationUniversity)
class AccommodationUniversityAdmin(admin.ModelAdmin):
    list_display = ('accommodation', 'university')
