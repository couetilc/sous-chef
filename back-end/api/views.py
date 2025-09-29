from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timezone

bootup_time = datetime.now(timezone.utc)

# Create your views here.
def index(request):
    return HttpResponse("<h1>Hello, World!</h1>")

def health_check(request):
    now = datetime.now(timezone.utc)
    current_time = now.isoformat()
    uptime = str(now - bootup_time)
    return JsonResponse({
        'status': 'healthy',
        'current_time': current_time,
        'uptime': uptime,
    })
