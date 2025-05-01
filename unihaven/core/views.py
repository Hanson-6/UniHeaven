import logging
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.utils import timezone
from django.http import HttpResponse
import os
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from .utils import AddressLookupService, validate_required_fields

from .models import (
    Accommodation, Member, Specialist, University,
    Reservation, Rating, Campus, Owner, ActionLog
)

from .serializers import (
    AccommodationSerializer, MemberSerializer, UniversitySerializer,
    CEDARSSpecialistSerializer, ReservationSerializer, RatingSerializer, CampusSerializer, ActionLogSerializer
)

logger = logging.getLogger(__name__)

class UniversityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for University model, providing CRUD operations.
    """
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    

# Using ViewSets to handle basic CRUD operations
class CampusViewSet(viewsets.ModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer

class AccommodationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Accommodation model, providing CRUD operations.
    """
    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'building_name', 'description', 'type', 'address']
    ordering_fields = ['monthly_rent', 'num_bedrooms', 'num_beds', 'available_from']

    def get_serializer_context(self):
            context = super().get_serializer_context()
            if self.action in ['create', 'update']:
                context['allow_existing_email'] = True
            return context
    def create(self, request, *args, **kwargs):
        # Handle building_name lookup if needed
        if (request.data.get('building_name') and
                not all([
                    request.data.get('latitude'),
                    request.data.get('longitude'),
                    request.data.get('geo_address')
                ])):
            try:
                building_name = request.data.get('building_name')
                location_data = AddressLookupService.lookup_address(building_name)
                print(location_data)
                if location_data:
                    request_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
                    request_data['latitude'] = location_data.get('latitude')
                    request_data['longitude'] = location_data.get('longitude')
                    request_data['geo_address'] = location_data.get('geo_address')
                else:
                    return Response(
                        {"error": "No address found for this building name. Please enter location data manually."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                logger.exception(f"Failed to get location data for building '{building_name}'")
                return Response(
                    {"error": f"Failed to get location data: {str(e)}. Please enter location data manually."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            request_data = request.data

        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        accommodation = serializer.save()
        
        # Log the creation action
        specialist_id = request.data.get('specialist_id')
        universities = request_data.get('universities', [])
        ActionLog.objects.create(
            action_type="CREATE_ACCOMMODATION",
            user_type="SPECIALIST" if specialist_id else "SYSTEM",
            user_id=specialist_id,
            accommodation_id=accommodation.id,
            details=f"Created accommodation '{accommodation.name}' with universities {universities}"
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Search for accommodations using query parameters.
        Supports filters such as type, availability, price range, and also optional sorting by distance.
        Filters by the logged-in member's university and excludes accommodations with overlapping reservations.
        """
        accommodation_type = request.query_params.get('type')
        available_from = request.query_params.get('available_from')
        available_to = request.query_params.get('available_to')
        num_beds = request.query_params.get('num_beds')
        num_bedrooms = request.query_params.get('num_bedrooms')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        campus_id = request.query_params.get('campus_id')
        sort_by = request.query_params.get('sort_by', 'distance')
        member_id = request.query_params.get('member_id')  # Get the member_id to determine the university
    
        # when search, we must have provide "/?member_id=<id:int>"
        if not member_id:
            return Response({"error": "member_id is required for searching accommodations"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            member = Member.objects.get(id=member_id)
            member_university = member.university
        except Member.DoesNotExist:
            return Response({"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND)

        # Step 2: Filter accommodations by the member's university
        queryset = Accommodation.objects.filter(
            universities=member_university,  # Only include accommodations associated with the member's university
            is_available=True
        )

        # Step 3: Apply filters
        if accommodation_type:
            queryset = queryset.filter(type=accommodation_type)
        if available_from:
            queryset = queryset.filter(available_from__lte=available_from)
        if available_to:
            queryset = queryset.filter(available_to__gte=available_to)
        if num_beds:
            queryset = queryset.filter(num_beds__gte=num_beds)
        if num_bedrooms:
            queryset = queryset.filter(num_bedrooms__gte=num_bedrooms)
        if min_price:
            queryset = queryset.filter(monthly_rent__gte=min_price)
        if max_price:
            queryset = queryset.filter(monthly_rent__lte=max_price)

        # Step 4: Exclude accommodations with overlapping reservations
        if available_from and available_to:
            queryset = queryset.exclude(
                reservation__reserved_from__lt=available_to,
                reservation__reserved_to__gt=available_from,
                reservation__status__in=['PENDING', 'CONFIRMED']
            ).distinct()

        # Step 5: Sorting
        if sort_by == 'price_asc':
            queryset = queryset.order_by('monthly_rent')
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-monthly_rent')
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        # Sorting by distance to a campus
        if campus_id:
            try:
                campus = Campus.objects.get(id=campus_id)
                # Calculate distance for each accommodation
                accommodations_with_distance = [
                    (accommodation, accommodation.calculate_distance(campus))
                    for accommodation in queryset
                ]
                accommodations_with_distance.sort(key=lambda x: x[1])
                data = []
                for accommodation, distance in accommodations_with_distance:
                    serializer = self.get_serializer(accommodation)
                    acc_data = serializer.data
                    acc_data['distance'] = round(distance, 2)
                    data.append(acc_data)
                return Response(data)
            except Campus.DoesNotExist:
                return Response({"error": "Campus not found"}, status=status.HTTP_404_NOT_FOUND)
                

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reserve(self, request, pk=None):
        """
        Reserve this accommodation.
        Expects fields: member_id, reserved_from, reserved_to, contact_name, contact_phone.
        """
        accommodation = self.get_object()
        if not accommodation.is_available:
            return Response({"error": "Accommodation not available"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_required_fields(request.data, ['member_id', 'reserved_from', 'reserved_to', 'contact_name', 'contact_phone'])
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ReservationSerializer(data={
            'accommodation': accommodation.id,
            'member': request.data.get('member_id'),
            'reserved_from': request.data.get('reserved_from'),
            'reserved_to': request.data.get('reserved_to'),
            'contact_name': request.data.get('contact_name'),
            'contact_phone': request.data.get('contact_phone'),
            'status': 'PENDING'
        })
        if serializer.is_valid():
            reservation = serializer.save()
            # Mark the accommodation as unavailable
            accommodation.is_available = False
            accommodation.save()
            # Log the action
            ActionLog.objects.create(
                action_type="CREATE_RESERVATION",
                user_type="MEMBER",
                user_id=reservation.member.id,
                accommodation_id=accommodation.id,
                reservation_id=reservation.id,
                details=f"Created reservation for '{accommodation.name}'"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_unavailable(self, request, pk=None):
        """
        Mark this accommodation as unavailable.
        Optionally log the specialist who performed the action.
        """
        accommodation = self.get_object()
        accommodation.is_available = False
        accommodation.save()
        specialist_id = request.data.get('specialist_id')
        if specialist_id:
            try:
                specialist = Specialist.objects.get(pk=specialist_id)
                ActionLog.objects.create(
                    action_type="MARK_UNAVAILABLE",
                    user_type="SPECIALIST",
                    user_id=specialist.id,
                    accommodation_id=accommodation.id,
                    details=f"Marked accommodation '{accommodation.name}' as unavailable"
                )
            except Specialist.DoesNotExist:
                ActionLog.objects.create(
                    action_type="MARK_UNAVAILABLE",
                    accommodation_id=accommodation.id,
                    details=f"Marked accommodation '{accommodation.name}' as unavailable"
                )
        else:
            ActionLog.objects.create(
                action_type="MARK_UNAVAILABLE",
                accommodation_id=accommodation.id,
                details=f"Marked accommodation '{accommodation.name}' as unavailable"
            )
        return Response({"status": "Accommodation marked as unavailable"}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        accommodation = self.get_object()
        active_reservations = Reservation.objects.filter(
            accommodation=accommodation,
            status__in=['PENDING', 'CONFIRMED']
        ).exists()
        if active_reservations:
            return Response({"error": "Cannot delete accommodation with active reservations"},
                            status=status.HTTP_400_BAD_REQUEST)
        name = accommodation.name
        self.perform_destroy(accommodation)
        specialist_id = request.data.get('specialist_id')
        if specialist_id:
            try:
                specialist = Specialist.objects.get(pk=specialist_id)
                ActionLog.objects.create(
                    action_type="DELETE_ACCOMMODATION",
                    user_type="SPECIALIST",
                    user_id=specialist.id,
                    details=f"Deleted accommodation '{name}'"
                )
            except Specialist.DoesNotExist:
                ActionLog.objects.create(
                    action_type="DELETE_ACCOMMODATION",
                    details=f"Deleted accommodation '{name}'"
                )
        else:
            ActionLog.objects.create(
                action_type="DELETE_ACCOMMODATION",
                details=f"Deleted accommodation '{name}'"
            )
        return Response({"status": f"Accommodation '{name}' successfully deleted"}, status=status.HTTP_200_OK)

class ReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Reservation model, providing CRUD operations.
    """
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancel a reservation if it is not yet confirmed.
        Changes status to 'CANCELLED' and marks the associated accommodation as available.
        """
        reservation = self.get_object()
        if reservation.status == 'CONFIRMED':
            return Response(
                {"error": "Cannot cancel a confirmed reservation"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = reservation.status
        reservation.status = 'CANCELLED'
        reservation.save()
        
        # Mark associated accommodation as available
        accommodation = reservation.accommodation
        accommodation.is_available = True
        accommodation.save()

        # Log the action for auditing
        ActionLog.objects.create(
            action_type="CANCEL_RESERVATION",
            user_type="MEMBER",
            user_id=reservation.member.id,
            accommodation_id=accommodation.id,
            reservation_id=reservation.id,
            details=f"Reservation cancelled; status changed from {old_status} to CANCELLED"
        )
        return Response(
            {"status": "Reservation cancelled successfully"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Update the status of a reservation.
        Expects a POST with a 'status' field representing the new status.
        """
        reservation = self.get_object()
        new_status = request.data.get('status')
        valid_statuses = [s[0] for s in Reservation.STATUS_CHOICES]
        if not new_status or new_status not in valid_statuses:
            return Response(
                {"error": "Invalid status value"},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = reservation.status
        reservation.status = new_status
        reservation.save()

        # Additional logic based on status change
        if new_status == 'CONFIRMED' and old_status == 'PENDING':
            # For example, notify the member that their reservation is confirmed.
            pass
        elif new_status == 'COMPLETED' and old_status != 'COMPLETED':
            # Perhaps enable rating for the reservation here.
            pass
        elif new_status == 'CANCELLED' and old_status != 'CANCELLED':
            # In case the reservation gets cancelled, mark accommodation as available.
            accommodation = reservation.accommodation
            accommodation.is_available = True
            accommodation.save()

        # Log the status update action
        ActionLog.objects.create(
            action_type="UPDATE_RESERVATION_STATUS",
            user_type="MEMBER",
            user_id=reservation.member.id,
            accommodation_id=reservation.accommodation.id,
            reservation_id=reservation.id,
            details=f"Reservation status updated from {old_status} to {new_status}"
        )

        serializer = ReservationSerializer(reservation)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Member model, providing CRUD operations.
    """
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    @action(detail=True, methods=['get'], url_path='reservations')
    def reservations(self, request, pk=None):
        member = self.get_object()
        reservations = Reservation.objects.filter(member=member)
        serializer = ReservationSerializer(reservations, many=True, context={'request': request})
        return Response(serializer.data)

class SpecialistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Specialist model, providing CRUD operations.
    """
    queryset = Specialist.objects.all()
    serializer_class = CEDARSSpecialistSerializer

class RatingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Rating model, providing read-only operations along with custom actions:
    - 'moderate': to moderate a specific rating.
    - 'pending': to retrieve all ratings that have not yet been moderated.
    """
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

    def get_queryset(self):
        queryset = Rating.objects.all()
        accommodation_id = self.request.query_params.get('accommodation')
        if accommodation_id:
            queryset = queryset.filter(accommodation__id=accommodation_id)
        return queryset

    @action(detail=True, methods=['post'], url_path='moderate')
    def moderate(self, request, pk=None):
        """
        Moderate a specific rating.
        
        Expects:
        - specialist_id: ID of the Specialist performing moderation.
        - is_approved: Boolean indicating approval (default is True).
        - moderation_note: Optional note explaining the decision.
        
        Returns the updated rating data along with a status message.
        """
        try:
            rating = self.get_object()
        except Rating.DoesNotExist:
            return Response(
                {"error": "Rating not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        specialist_id = request.data.get('specialist_id')
        if not specialist_id:
            return Response(
                {"error": "Specialist ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            specialist = Specialist.objects.get(pk=specialist_id)
        except Specialist.DoesNotExist:
            return Response(
                {"error": "Specialist not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_approved = request.data.get('is_approved', True)
        moderation_note = request.data.get('moderation_note', '')
        
        rating.is_approved = is_approved
        rating.moderated_by = specialist
        rating.moderation_date = timezone.now()
        rating.moderation_note = moderation_note
        rating.save()
        
        # Log the moderation action for auditing purposes.
        ActionLog.objects.create(
            action_type="MODERATE_RATING",
            user_type="SPECIALIST",
            user_id=specialist.id,
            accommodation_id=rating.accommodation.id,
            rating_id=rating.id,
            details=f"Rating {'approved' if is_approved else 'rejected'}: {moderation_note}"
        )
        
        serializer = self.get_serializer(rating)
        return Response({
            "status": f"Rating {'approved' if is_approved else 'rejected'}",
            "rating": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """
        Retrieve all ratings that have not yet been moderated.
        This endpoint returns ratings where 'moderated_by' is null, ordered by the creation time.
        """
        pending_ratings = Rating.objects.filter(moderated_by__isnull=True).order_by('created_at')
        # Set up the paginator
        paginator = PageNumberPagination()
        paginator.page_size = 10  # or your desired page size
        page = paginator.paginate_queryset(pending_ratings, request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def get_action_logs(request):
    """
    Get a list of action logs for audit purposes.
    """
    # Parse filtering parameters
    action_type = request.query_params.get('action_type')
    user_type = request.query_params.get('user_type')
    user_id = request.query_params.get('user_id')
    accommodation_id = request.query_params.get('accommodation_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Start with all logs
    logs = ActionLog.objects.all()
    
    # Apply filters
    if action_type:
        logs = logs.filter(action_type=action_type)
    if user_type:
        logs = logs.filter(user_type=user_type)
    if user_id:
        logs = logs.filter(user_id=user_id)
    if accommodation_id:
        logs = logs.filter(accommodation_id=accommodation_id)
    if start_date:
        logs = logs.filter(created_at__gte=start_date)
    if end_date:
        logs = logs.filter(created_at__lte=end_date)
    
    # Pagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    result_page = paginator.paginate_queryset(logs, request)
    if not result_page:
        return Response({"error": "No logs found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ActionLogSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

def serve_static_schema(request):
    with open(os.path.join(settings.BASE_DIR, 'schema.yaml'), 'r') as f:
        schema_content = f.read()
    return HttpResponse(schema_content, content_type='application/yaml')