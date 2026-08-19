from django.http import JsonResponse


def api_home(request):
    return JsonResponse({
        "status": "success",
        "message": "JH Classes API is running"
    })
