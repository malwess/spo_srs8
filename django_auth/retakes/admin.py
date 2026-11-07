from django.contrib import admin

from .models import RetakeEvent, RetakeRequest, RetakeSlot


@admin.register(RetakeSlot)
class RetakeSlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'starts_at', 'room', 'capacity', 'booked')
    list_filter = ('course',)


class EventInline(admin.TabularInline):
    model = RetakeEvent
    extra = 0
    readonly_fields = ('action', 'actor', 'old_status', 'new_status', 'details', 'created_at')
    can_delete = False


@admin.register(RetakeRequest)
class RetakeRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'slot', 'status', 'created_at')
    list_filter = ('status', 'slot__course')
    inlines = [EventInline]
