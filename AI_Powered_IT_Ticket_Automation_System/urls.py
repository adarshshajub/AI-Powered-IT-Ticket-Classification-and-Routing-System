from django.contrib import admin
from django.urls import path, include
from .views import custom_400, custom_403, custom_404, custom_500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tickets.urls')),
]


c = 'AI_Powered_IT_Ticket_Automation_System.views.custom_400'
handler403 = 'AI_Powered_IT_Ticket_Automation_System.views.custom_403'
handler404 = 'AI_Powered_IT_Ticket_Automation_System.views.custom_404'
handler500 = 'AI_Powered_IT_Ticket_Automation_System.views.custom_500'