from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landingpage', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='customuser',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_superuser=True),
                fields=('is_superuser',),
                name='only_one_super_admin',
            ),
        ),
    ]
