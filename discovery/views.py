from django.http import JsonResponse
from discovery.processor.gnmi_util import topology

# Create your views here.


def start_discovery(request):
    return JsonResponse(topology)
    