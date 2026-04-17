from django.db import connection

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'organization') and request.user.organization:
            schema = request.user.organization.schema
            # We use a list to ensure public is always available for shared tables
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema}, public")
        else:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")

        response = self.get_response(request)
        return response
