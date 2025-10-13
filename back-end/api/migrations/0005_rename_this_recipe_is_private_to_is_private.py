from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_dietaryingredient"),
    ]

    operations = [
        # The model currently defines `is_private` but the existing DB column
        # is `this_recipe_is_private`. Rename the column at the DB level so
        # it matches the model. The operation is reversible.
        migrations.RunSQL(
            sql=(
                "ALTER TABLE api_recipe RENAME COLUMN this_recipe_is_private TO is_private;"
            ),
            reverse_sql=(
                "ALTER TABLE api_recipe RENAME COLUMN is_private TO this_recipe_is_private;"
            ),
        ),
    ]
