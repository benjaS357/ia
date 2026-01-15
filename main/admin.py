from django.contrib import admin
from .models import ChatMessage

# Register your models here.

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['role', 'message_preview', 'timestamp', 'session_id']
    list_filter = ['role', 'timestamp']
    search_fields = ['message', 'session_id']
    date_hierarchy = 'timestamp'
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Mensaje'
