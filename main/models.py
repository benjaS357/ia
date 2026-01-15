from django.db import models
from django.utils import timezone

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
