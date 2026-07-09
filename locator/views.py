import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from locator.models import ServiceUnit, Incident
from locator.forms import UploadDatasetForm
from locator import services

@ensure_csrf_cookie
def home(request):
    """
    Renders the Emergency Response Locator dashboard homepage.
    """
    ambulances = ServiceUnit.objects.filter(unit_type='Ambulance').count()
    fire_stations = ServiceUnit.objects.filter(unit_type='Fire').count()
    police_units = ServiceUnit.objects.filter(unit_type='Police').count()
    
    available_units = ServiceUnit.objects.filter(status='Available').count()
    non_available_units = ServiceUnit.objects.exclude(status='Available').count()
    
    dataset_incidents = Incident.objects.filter(source='dataset').count()

    context = {
        'ambulances': ambulances,
        'fire_stations': fire_stations,
        'police_units': police_units,
        'available_units': available_units,
        'non_available_units': non_available_units,
        'dataset_incidents': dataset_incidents,
        'upload_form': UploadDatasetForm(),
    }
    return render(request, 'home.html', context)


@require_POST
def upload_dataset(request):
    """
    Receives text dataset via file upload (AJAX), delegates processing to service layer,
    and returns a summary of the uploaded records and parsed warnings.
    """
    form = UploadDatasetForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': "Invalid file upload. Please select a valid .txt file."
        }, status=400)

    uploaded_file = request.FILES['dataset_file']

    try:
        units_count, incidents_count, warnings = services.handle_dataset_upload(uploaded_file)
        
        # Calculate updated dashboard stats to return in JSON so frontend can update immediately
        ambulances = ServiceUnit.objects.filter(unit_type='Ambulance').count()
        fire_stations = ServiceUnit.objects.filter(unit_type='Fire').count()
        police_units = ServiceUnit.objects.filter(unit_type='Police').count()
        available_units = ServiceUnit.objects.filter(status='Available').count()
        non_available_units = ServiceUnit.objects.exclude(status='Available').count()
        dataset_incidents = Incident.objects.filter(source='dataset').count()

        return JsonResponse({
            'success': True,
            'units_count': units_count,
            'incidents_count': incidents_count,
            'warnings': warnings,
            'stats': {
                'ambulances': ambulances,
                'fire_stations': fire_stations,
                'police_units': police_units,
                'available_units': available_units,
                'non_available_units': non_available_units,
                'dataset_incidents': dataset_incidents
            }
        })

    except services.ParseError as e:
        return JsonResponse({'success': False, 'error': f"Parse Error: {str(e)}"}, status=400)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f"Validation Error: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f"An error occurred: {str(e)}"}, status=500)


@require_GET
def list_incidents(request):
    """
    Returns a list of all dataset-sourced incidents for the UI selection dropdown.
    """
    incidents = Incident.objects.filter(source='dataset').order_by('name')
    data = [
        {
            'id': inc.id,
            'name': inc.name,
            'latitude': inc.latitude,
            'longitude': inc.longitude
        }
        for inc in incidents
    ]
    return JsonResponse(data, safe=False)


@require_GET
def list_units(request):
    """
    Returns a list of all emergency service units in the database.
    """
    units = ServiceUnit.objects.all().order_by('unit_id')
    data = [
        {
            'unit_id': u.unit_id,
            'unit_type': u.unit_type,
            'latitude': u.latitude,
            'longitude': u.longitude,
            'status': u.status
        }
        for u in units
    ]
    return JsonResponse(data, safe=False)


@require_POST
def find_nearest(request):
    """
    Accepts JSON body specifying coordinates or incident ID, resolves the location,
    finds the closest available unit, and returns the result card data.
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON request body.'}, status=400)

    service_type = payload.get('service')
    if not service_type:
        return JsonResponse({'error': "Missing required field 'service'."}, status=400)

    try:
        # Resolve location coordinates and label
        lat, lon, label = services.resolve_incident(payload)
        
        # Dispatch nearest service calculation
        result = services.get_nearest_unit_for_incident(lat, lon, service_type, label)
        
        return JsonResponse(result)

    except services.NoIncidentFound as e:
        return JsonResponse({'error': str(e)}, status=404)
    except services.NoAvailableUnits as e:
        return JsonResponse({'error': str(e)}, status=404)
    except services.InvalidService as e:
        return JsonResponse({'error': str(e)}, status=400)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f"Failed to calculate nearest unit: {str(e)}"}, status=500)
