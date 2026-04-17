from django.core.management.base import BaseCommand
from accounts.models import Organization, User
from django.db import connection

class Command(BaseCommand):
    help = 'Seeds the database with a default organization and user'

    def handle(self, *args, **kwargs):
        # 1. Create organization via raw SQL to ensure it exists in tbl_organizacoes
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public")
            cursor.execute("""
                INSERT INTO public.tbl_organizacoes (numero, nome, schema)
                VALUES (1, 'Safira Softwares', 'org_0001')
                ON CONFLICT (numero) DO NOTHING
            """)

            # Create the schema for the organization
            cursor.execute("CREATE SCHEMA IF NOT EXISTS org_0001")

            # Popula o schema (Opcional, mas bom para isolamento)
            try:
                with open("schema/schema_base.sql", "r", encoding="utf-8") as f:
                    sql = f.read()
                cursor.execute("SET search_path TO org_0001")
                cursor.execute(sql)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not populate schema: {e}"))

            # Set search path back to public for Django's model queries
            cursor.execute("SET search_path TO public")

        # 2. Link to Organization model
        org = Organization.objects.get(numero=1)

        # 3. Create User
        email = 'suporte@safirasoftwares.inf.br'
        if not User.objects.filter(email=email).exists():
            User.objects.create_user(
                email=email,
                password='safira',
                organization=org
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created user {email}'))
        else:
            self.stdout.write(self.style.WARNING(f'User {email} already exists'))
