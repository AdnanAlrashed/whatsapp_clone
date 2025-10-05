from django.contrib import admin
from .models import Call

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ('caller', 'receiver', 'call_type', 'status', 'timestamp', 'duration_display')
    list_filter = ('call_type', 'status', 'timestamp')
    search_fields = ('caller__email', 'receiver__email')
    readonly_fields = ('timestamp', 'ended_at', 'duration')
    date_hierarchy = 'timestamp'
    
    def duration_display(self, obj):
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:02d}"
        return "---"
    duration_display.short_description = 'المدة'