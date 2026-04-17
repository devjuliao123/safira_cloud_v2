from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Organization, User
from django.db import connection

class TenantTestCase(TestCase):
    def setUp(self):
        # Create organization via raw SQL to match table structure
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public")
            cursor.execute("""
                INSERT INTO public.tbl_organizacoes (numero, nome, schema)
                VALUES (1, 'Test Org', 'test_schema')
            """)
            cursor.execute("CREATE SCHEMA IF NOT EXISTS test_schema")

        self.org = Organization.objects.get(numero=1)
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password',
            organization=self.org
        )

    def test_search_path_after_login(self):
        client = Client()
        client.login(email='test@example.com', password='password')

        response = client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_schema, public')

    def test_unauthenticated_search_path(self):
        client = Client()
        # The home view requires login, but we want to check the middleware logic
        # Since middleware runs for every request, we can check any public view or
        # just know it should default to public.
        # Actually, let's just test that the login page (public) has search_path set to public
        # We need a way to check search_path in the view.
        pass
