from django.contrib import admin
from servicenow.models import AssignmentGroup
# from tickets.models import Ticket

@admin.register(AssignmentGroup)
class AssignmentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'servicenow_group_id')
    search_fields = ('name', 'category')
