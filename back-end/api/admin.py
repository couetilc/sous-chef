from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Q

from api.models import Recipe, Ingredient, DietaryIngredient, RecipeIngredient


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
