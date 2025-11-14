from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0030_alter_curatedingredient_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='deliciousness_score',
            field=models.DecimalField(decimal_places=2, default=0, help_text='LLM-assessed deliciousness score from 0-100', max_digits=5),
        ),
    ]
