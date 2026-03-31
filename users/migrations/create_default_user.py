from django.db import migrations


def create_default_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    if not User.objects.filter(username='anasse').exists():
        User.objects.create_user(
            username='anasse',
            password='anasse',
        )


def delete_default_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.filter(username='anasse').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),  # dépend de l'app auth de Django, pas de users
    ]

    operations = [
        migrations.RunPython(create_default_user, delete_default_user),
    ]