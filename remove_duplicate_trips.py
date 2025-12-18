from core.models import Trip
from django.db.models import Count

# Find and delete duplicate trips based on trip_number
duplicates = Trip.objects.values('trip_number').annotate(count=Count('id')).filter(count__gt=1)

for duplicate in duplicates:
    trip_number = duplicate['trip_number']
    trips = Trip.objects.filter(trip_number=trip_number).order_by('id')
    # Keep the first one, delete the rest
    trips[1:].delete()
    print(f"Removed duplicates for trip: {trip_number}")

print("Duplicate trips removed successfully!")