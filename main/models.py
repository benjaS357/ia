from django.db import models
from django.utils import timezone
import json

# Create your models here.

class ChatMessage(models.Model):
    """Modelo para almacenar el historial de mensajes del chat con Gemini"""
    ROLE_CHOICES = [
        ('user', 'Usuario'),
        ('assistant', 'Asistente'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = "Mensaje de Chat"
        verbose_name_plural = "Mensajes de Chat"
    
    def __str__(self):
        return f"{self.role}: {self.message[:50]}..."


class QueryCache(models.Model):
    """Caché de consultas SAP para investigación acumulativa"""
    session_id = models.CharField(max_length=100, db_index=True)
    query_type = models.CharField(max_length=100)  # "Invoices", "Items", etc.
    query_description = models.TextField()  # Descripción legible de la consulta
    query_params = models.JSONField()  # Parámetros de la consulta
    result_data = models.JSONField()  # Resultados de la consulta
    result_summary = models.TextField(blank=True)  # Resumen generado por IA
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Consulta Cacheada"
        verbose_name_plural = "Consultas Cacheadas"
        indexes = [
            models.Index(fields=['session_id', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.query_type} - {self.query_description[:50]}"
        return f"{self.role}: {self.message[:50]}..."
