from django.db import models

class ServiceUnit(models.Model):
    """
    Represents an emergency response unit, which can be an Ambulance, Fire Station, or Police Vehicle.
    """
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Busy', 'Busy'),
        ('Maintenance', 'Maintenance'),
    ]
    
    UNIT_TYPES = [
        ('Ambulance', 'Ambulance'),
        ('Fire', 'Fire'),
        ('Police', 'Police'),
    ]

    unit_id = models.CharField(max_length=50, unique=True, db_index=True)
    unit_type = models.CharField(max_length=50, choices=UNIT_TYPES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Available')

    def __str__(self):
        return f"{self.unit_id} ({self.unit_type}) - {self.status}"


class Incident(models.Model):
    """
    Represents an emergency incident location. Can be loaded from a dataset or input manually.
    """
    SOURCE_CHOICES = [
        ('dataset', 'Dataset'),
        ('manual', 'Manual'),
    ]

    name = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='dataset')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or 'Manual Incident'} ({self.latitude}, {self.longitude})"


class SearchHistory(models.Model):
    """
    Records a history of incident searches and the unit assigned.
    """
    incident_lat = models.FloatField()
    incident_lon = models.FloatField()
    assigned_unit = models.ForeignKey(ServiceUnit, on_delete=models.SET_NULL, null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        unit_info = self.assigned_unit.unit_id if self.assigned_unit else "None"
        return f"Incident at ({self.incident_lat}, {self.incident_lon}) -> Unit: {unit_info} ({self.distance_km} km)"
