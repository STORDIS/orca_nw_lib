from django.http import JsonResponse
from discovery.processor.sonic_grpc import topology

# Create your views here.


def start_discovery(request):
    return JsonResponse(topology)
    