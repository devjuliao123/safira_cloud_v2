from django.db import migrations

def create_organizations_table(apps, schema_editor):
    # Check if we are on a PostgreSQL backend to use SERIAL, else use AUTOINCREMENT or just let it fail gracefully
    schema_editor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_organizacoes (
            id SERIAL PRIMARY KEY,
            numero INT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            schema TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_organizations_table),
    ]
