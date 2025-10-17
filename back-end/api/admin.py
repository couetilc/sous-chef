from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from django.utils.html import format_html

from api.models import Recipe, Ingredient, DietaryIngredient, RecipeIngredient, ScrapedInventory, ScrapedRecipe, ScrapedIngredient, ScrapedNutritionalInfo


class IngredientInline(admin.TabularInline):
	"""Show recipe ingredients inline on the Recipe admin page."""
	model = RecipeIngredient
	extra = 0


class RestrictedForUserFilter(SimpleListFilter):
	"""
	Custom filter to show recipes that contain ingredients restricted by a selected user.
	This filter adds a dropdown of users (by username) and filters recipes that include
	any ingredient the selected user has marked as restricted.
	"""
	title = 'restricted for user'
	parameter_name = 'restricted_for_user'

	def lookups(self, request, model_admin):
		# Import here to avoid heavy imports at module-load time if auth isn't used elsewhere
		from django.contrib.auth import get_user_model

		User = get_user_model()
		users = User.objects.all().order_by('username')[:200]
		# Use pk and get_username() to satisfy static checkers that don't know user fields
		return [(str(u.pk), u.get_username()) for u in users]

	def queryset(self, request, queryset):
		val = self.value()
		if not val:
			return queryset

		# Filter recipes that contain ingredients restricted by the user with id=val
		return queryset.filter(
			ingredients_list__ingredient__dietary_restrictions__user__id=val
		).distinct()

class CaloriesRangeFilter(SimpleListFilter):
    title = 'calories'
    parameter_name = 'calories_range'

    def lookups(self, request, model_admin):
        return [
            ('0-100', '0–100'),
            ('101-200', '101–200'),
            ('201-300', '201–300'),
            ('301-400', '301–400'),
            ('401+', '401+'),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset

        if val == '0-100':
            return queryset.extra(
                where=["CAST(calories AS FLOAT) BETWEEN %s AND %s"],
                params=[0, 100]
            )
        elif val == '101-200':
            return queryset.extra(
                where=["CAST(calories AS FLOAT) BETWEEN %s AND %s"],
                params=[101, 200]
            )
        elif val == '201-300':
            return queryset.extra(
                where=["CAST(calories AS FLOAT) BETWEEN %s AND %s"],
                params=[201, 300]
            )
        elif val == '301-400':
            return queryset.extra(
                where=["CAST(calories AS FLOAT) BETWEEN %s AND %s"],
                params=[301, 400]
            )
        elif val == '401+':
            return queryset.extra(
                where=["CAST(calories AS FLOAT) >= %s"],
                params=[401]
            )

        return queryset

class ProteinRangeFilter(SimpleListFilter):
    title = 'protein (g)'
    parameter_name = 'protein_range'

    def lookups(self, request, model_admin):
        return [
            ('0-5', '0–5 g'),
            ('6-10', '6–10 g'),
            ('11-15', '11–15 g'),
            ('16-20', '16–20 g'),
            ('21+', '21+ g'),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset

        if val == '0-5':
            return queryset.extra(
                where=["CAST(protein_g AS FLOAT) BETWEEN %s AND %s"],
                params=[0, 5]
            )
        elif val == '6-10':
            return queryset.extra(
                where=["CAST(protein_g AS FLOAT) BETWEEN %s AND %s"],
                params=[6, 10]
            )
        elif val == '11-15':
            return queryset.extra(
                where=["CAST(protein_g AS FLOAT) BETWEEN %s AND %s"],
                params=[11, 15]
            )
        elif val == '16-20':
            return queryset.extra(
                where=["CAST(protein_g AS FLOAT) BETWEEN %s AND %s"],
                params=[16, 20]
            )
        elif val == '21+':
            return queryset.extra(
                where=["CAST(protein_g AS FLOAT) >= %s"],
                params=[21]
            )

        return queryset

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_private', 'created_at', 'updated_at')
	search_fields = ('title', 'instructions', 'ingredients')
	list_filter = ('is_private', 'created_at', RestrictedForUserFilter)
	inlines = (IngredientInline,)
	ordering = ('-created_at',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)
	ordering = ('name',)


@admin.register(DietaryIngredient)
class DietaryIngredientAdmin(admin.ModelAdmin):
	list_display = ('ingredient', 'user')
	search_fields = ('ingredient__name', 'user__username')
	list_filter = ('ingredient', 'user')


# Optionally register RecipeIngredient for direct inspection in admin
@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
	list_display = ('recipe', 'ingredient', 'quantity')
	search_fields = ('recipe__title', 'ingredient__name')
	list_filter = ('ingredient',)

#food_id,ingredient_name,quantity_other,quantity_oz,price
@admin.register(ScrapedInventory)
class ScrapedInventory(admin.ModelAdmin):
	list_display = ('food_id', 'ingredient_name', 'quantity_other', 'quantity_oz', 'price')
	search_fields = ('ingredient_name', 'price')
	list_filter = ('ingredient_name', 'price')

@admin.register(ScrapedRecipe)
class ScrapedRecipe(admin.ModelAdmin):
	list_display = ('title', 'url', 'image', 'ingredients', 'steps')
	search_fields = ('title', 'ingredients', 'steps')
	list_filter = ('title',)

@admin.register(ScrapedIngredient)
class ScrapedIngredient(admin.ModelAdmin):
	list_display = ('description', 'food_category')
	search_fields = ('description', 'food_category')
	list_filter = ('description', 'food_category')

@admin.register(ScrapedNutritionalInfo)
class ScrapedNutritionalInfo(admin.ModelAdmin):
	list_display = ('description', 'calories', "protein_g", "fat_g", "carbs_g")
	search_fields = ('description', 'calories', "protein_g", "fat_g", "carbs_g")
	list_filter = (CaloriesRangeFilter, ProteinRangeFilter)
