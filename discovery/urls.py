from django.urls import path
#from discovery import views
from discovery.views import start_discovery

urlpatterns = [
    path('start_discovery/', start_discovery),
]