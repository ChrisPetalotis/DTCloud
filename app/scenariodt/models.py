from django.db import models
from rdflib import Graph, URIRef, Namespace

class Notification(models.Model):
    message = models.CharField(max_length=200)
    date_time = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.message