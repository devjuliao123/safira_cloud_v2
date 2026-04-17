from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import connection

@login_required
def home(request):
    with connection.cursor() as cursor:
        cursor.execute("SHOW search_path")
        search_path = cursor.fetchone()[0]

    return render(request, 'accounts/home.html', {
        'search_path': search_path,
        'organization': request.user.organization
    })
