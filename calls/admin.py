from django.contrib import admin
from .models import Call

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ['caller', 'receiver', 'call_type', 'status', 'is_active', 'timestamp']
    list_filter = ['call_type', 'status', 'is_active', 'timestamp']
    search_fields = ['caller__email', 'receiver__email']
    list_editable = ['status', 'is_active']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('معلومات المكالمة', {
            'fields': ('caller', 'receiver', 'call_type', 'status')
        }),
        ('توقيت المكالمة', {
            'fields': ('timestamp', 'ended_at', 'duration'),
            'classes': ('collapse',)
        }),
        ('الحالة', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ['timestamp', 'ended_at', 'duration']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('caller', 'receiver')