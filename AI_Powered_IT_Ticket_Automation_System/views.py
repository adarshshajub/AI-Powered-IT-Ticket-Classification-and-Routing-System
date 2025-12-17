from django.shortcuts import render

def custom_400(request, exception):
    """Custom 400 Bad Request view"""
    return render(request, '400.html', status=400)

def custom_403(request, exception):
    """Custom 403 Forbidden view"""
    return render(request, '403.html', status=403)

def custom_404(request, exception):
    """Custom 404 Page Not Found view"""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 Internal Server Error view"""
    return render(request, '500.html', status=500)