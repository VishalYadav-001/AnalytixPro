from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_analysis_cleaned_file_analysis_top_kpis_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatsession',
            name='download_code',
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
    ]
