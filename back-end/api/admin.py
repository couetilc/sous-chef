from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from django.urls import reverse
from django.utils.html import format_html
from decimal import Decimal

from api.models import Recipe, Ingredient, DietaryIngredient, RecipeIngredient, ScrapedInventory, ScrapedRecipe, ScrapedIngredient, ScrapedNutritionalInfo, CookedRecipe, Meal, ChatConversation, ChatMessage, CuratedIngredient, RecipeCuratedIngredient


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

class PriceRangeFilter(SimpleListFilter):
    title = 'price'
    parameter_name = 'price_range'

    def lookups(self, request, model_admin):
        return [
            ('missing', 'Missing'),
            ('0-0.99', '$0.00–$0.99'),
            ('1-2.99', '$1.00–$2.99'),
            ('3-4.99', '$3.00–$4.99'),
            ('5-9.99', '$5.00–$9.99'),
            ('10-19.99', '$10.00–$19.99'),
            ('20+', '$20.00+'),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if not v:
            return queryset
        if v == 'missing':
            return queryset.filter(price__isnull=True)

        bounds = {
            '0-0.99':   (Decimal('0.00'),  Decimal('0.99')),
            '1-2.99':   (Decimal('1.00'),  Decimal('2.99')),
            '3-4.99':   (Decimal('3.00'),  Decimal('4.99')),
            '5-9.99':   (Decimal('5.00'),  Decimal('9.99')),
            '10-19.99': (Decimal('10.00'), Decimal('19.99')),
            '20+':      (Decimal('20.00'), None),
        }
        lo, hi = bounds[v]
        qs = queryset
        if lo is not None:
            qs = qs.filter(price__gte=lo)
        if hi is not None:
            qs = qs.filter(price__lte=hi)
        return qs

class DeliciousnessScoreFilter(SimpleListFilter):
    """Filter recipes by deliciousness score ranges"""
    title = 'deliciousness score'
    parameter_name = 'deliciousness_range'

    def lookups(self, request, model_admin):
        return [
            ('unscored', 'Unscored (0)'),
            ('0-49', '0–49 (Unappealing)'),
            ('50-69', '50–69 (Forgettable)'),
            ('70-84', '70–84 (Tasty)'),
            ('85-92', '85–92 (Crowd-pleasing)'),
            ('93-100', '93–100 (Exceptional)'),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset

        if val == 'unscored':
            return queryset.filter(deliciousness_score=0)
        elif val == '0-49':
            return queryset.filter(deliciousness_score__gte=0.01, deliciousness_score__lte=49)
        elif val == '50-69':
            return queryset.filter(deliciousness_score__gte=50, deliciousness_score__lte=69)
        elif val == '70-84':
            return queryset.filter(deliciousness_score__gte=70, deliciousness_score__lte=84)
        elif val == '85-92':
            return queryset.filter(deliciousness_score__gte=85, deliciousness_score__lte=92)
        elif val == '93-100':
            return queryset.filter(deliciousness_score__gte=93, deliciousness_score__lte=100)

        return queryset

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
	list_display = ('title', 'deliciousness_score', 'score_notes_preview', 'is_private', 'created_at', 'updated_at')
	search_fields = ('title', 'instructions', 'ingredients', 'deliciousness_notes')
	list_filter = ('is_private', DeliciousnessScoreFilter, 'created_at', RestrictedForUserFilter)
	inlines = (IngredientInline,)
	ordering = ('-deliciousness_score', '-created_at')
	readonly_fields = ('created_at', 'updated_at', 'deliciousness_notes_display')

	def score_notes_preview(self, obj):
		"""Show first 40 chars of deliciousness notes"""
		if obj.deliciousness_notes:
			preview = obj.deliciousness_notes[:40]
			if len(obj.deliciousness_notes) > 40:
				preview += '...'
			return preview
		return '-'
	score_notes_preview.short_description = 'Score Notes'
	score_notes_preview.admin_order_field = 'deliciousness_notes'

	def deliciousness_notes_display(self, obj):
		"""Display full deliciousness notes in detail view"""
		if obj.deliciousness_notes:
			return format_html(
				'<div style="padding: 10px; background-color: #f8f9fa; border-left: 4px solid #28a745; border-radius: 4px;">'
				'<strong>Score:</strong> {}<br>'
				'<strong>Notes:</strong> {}'
				'</div>',
				obj.deliciousness_score,
				obj.deliciousness_notes
			)
		return 'No notes available'
	deliciousness_notes_display.short_description = 'Deliciousness Assessment'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
	list_display = ('name', 'calories', 'protein_g', 'fat_g', 'carbs_g')
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


# Curated Ingredient Admin

@admin.register(CuratedIngredient)
class CuratedIngredientAdmin(admin.ModelAdmin):
	list_display = ('name', 'is_approved', 'created_at')
	search_fields = ('name',)
	list_filter = ('is_approved', 'created_at')
	ordering = ('name',)
	readonly_fields = ('created_at',)
	actions = ['approve_ingredients', 'unapprove_ingredients']

	def approve_ingredients(self, request, queryset):
		"""Bulk action to approve selected curated ingredients"""
		updated = queryset.update(is_approved=True)
		self.message_user(request, f'{updated} curated ingredient(s) successfully approved.')
	approve_ingredients.short_description = 'Approve selected curated ingredients'

	def unapprove_ingredients(self, request, queryset):
		"""Bulk action to unapprove selected curated ingredients"""
		updated = queryset.update(is_approved=False)
		self.message_user(request, f'{updated} curated ingredient(s) unapproved.')
	unapprove_ingredients.short_description = 'Unapprove selected curated ingredients'


@admin.register(RecipeCuratedIngredient)
class RecipeCuratedIngredientAdmin(admin.ModelAdmin):
	list_display = ('recipe_title', 'curated_ingredient', 'created_at')
	search_fields = ('recipe__title', 'curated_ingredient__name')
	list_filter = ('curated_ingredient', 'created_at')
	ordering = ('recipe', 'curated_ingredient__name')
	readonly_fields = ('created_at',)

	def recipe_title(self, obj):
		"""Display recipe title with link"""
		url = reverse('admin:api_recipe_change', args=[obj.recipe.pk])
		return format_html('<a href="{}">{}</a>', url, obj.recipe.title)
	recipe_title.short_description = 'Recipe'
	recipe_title.admin_order_field = 'recipe__title'


@admin.register(ScrapedInventory)
class ScrapedInventoryAdmin(admin.ModelAdmin):
    list_display = ('food_id', 'ingredient_name', 'quantity_other', 'quantity_oz', 'price')
    search_fields = ('ingredient_name',)
    list_filter = (PriceRangeFilter,)
    ordering = ('ingredient_name',)

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

@admin.register(CookedRecipe)
class CookedRecipeAdmin(admin.ModelAdmin):
	list_display = ('user', 'recipe', 'cooked_at')
	search_fields = ('user__username', 'recipe__title')
	list_filter = ('cooked_at', 'user')
	ordering = ('-cooked_at',)

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('cooked_recipe', 'servings', 'eaten_at')
    search_fields = ('cooked_recipe__recipe__title', 'cooked_recipe__user__username')
    list_filter = ('eaten_at',)
    ordering = ('-eaten_at',)


# AI Chat Admin
class HasToolCallsFilter(SimpleListFilter):
    """Custom filter to show messages with or without tool calls"""
    title = 'has tool calls'
    parameter_name = 'has_tool_calls'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(tool_calls__isnull=True).exclude(tool_calls=[])
        if self.value() == 'no':
            return queryset.filter(Q(tool_calls__isnull=True) | Q(tool_calls=[]))
        return queryset


class ChatMessageInline(admin.TabularInline):
    """Show chat messages inline on the ChatConversation admin page."""
    model = ChatMessage
    extra = 0
    fields = ('role', 'content_preview', 'has_tool_calls', 'created_at')
    readonly_fields = ('role', 'content_preview', 'has_tool_calls', 'created_at')
    can_delete = False

    def content_preview(self, obj):
        """Show first 100 chars of message content with link to detail page"""
        if obj.content:
            preview = obj.content[:100]
            if len(obj.content) > 100:
                preview += '...'
        else:
            preview = ''

        if obj.pk:
            url = reverse('admin:api_chatmessage_change', args=[obj.pk])
            return format_html('<a href="{}">{}</a>', url, preview if preview else '(empty)')
        return preview
    content_preview.short_description = 'Content'

    def has_tool_calls(self, obj):
        """Show if message has associated tool calls"""
        if obj.tool_calls:
            return '✓'
        return '✗'
    has_tool_calls.short_description = 'Tools'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_active', 'message_count', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'message_count', 'full_conversation')
    inlines = (ChatMessageInline,)
    ordering = ('-updated_at',)

    def message_count(self, obj):
        """Display the number of messages in the conversation"""
        return obj.messages.count()
    message_count.short_description = 'Messages'

    def full_conversation(self, obj):
        """Display the full conversation in a readable format"""
        import json
        messages = obj.messages.all()
        if not messages:
            return format_html('<p><em>No messages yet</em></p>')

        html = '<div style="font-family: monospace; white-space: pre-wrap;">'
        for msg in messages:
            role_color = '#2196F3' if msg.role == 'user' else '#4CAF50'
            html += f'<div style="margin-bottom: 15px; padding: 10px; background: var(--body-bg); border-left: 3px solid {role_color};">'
            html += f'<strong style="color: {role_color};">{msg.role.upper()}</strong> '
            html += f'<span style="color: var(--body-quiet-color); font-size: 0.9em;">({msg.created_at.strftime("%Y-%m-%d %H:%M:%S")})</span>'

            # Show tool call indicator if present
            if msg.tool_calls:
                html += f' <span style="background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">🔧 Tool Call</span>'

            html += '<br>'
            html += f'{msg.content}'

            # Show tool call details if present
            if msg.tool_calls:
                html += '<div style="margin-top: 10px; padding: 8px; background: #f0f8ff; border-radius: 4px; font-size: 0.85em;">'
                for i, tool_call in enumerate(msg.tool_calls):
                    tool_name = tool_call.get('tool_name', 'Unknown')
                    parameters = tool_call.get('parameters', {})
                    # Escape curly braces for format_html by doubling them
                    params_json = json.dumps(parameters).replace('{', '{{').replace('}', '}}')
                    html += f'<strong>Tool:</strong> {tool_name}<br>'
                    html += f'<strong>Params:</strong> {params_json}<br>'
                html += '</div>'

            html += '</div>'
        html += '</div>'
        return format_html(html)
    full_conversation.short_description = 'Full Conversation'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation_user', 'role', 'content_preview', 'has_tool_calls', 'created_at')
    search_fields = ('conversation__user__username', 'content')
    list_filter = ('role', 'created_at', 'conversation__user', HasToolCallsFilter)
    readonly_fields = ('conversation', 'role', 'content', 'tool_calls_display', 'created_at')
    ordering = ('-created_at',)

    def conversation_user(self, obj):
        """Display which user this message belongs to"""
        return obj.conversation.user.username
    conversation_user.short_description = 'User'
    conversation_user.admin_order_field = 'conversation__user__username'

    def content_preview(self, obj):
        """Show first 100 chars of message content"""
        if obj.content:
            preview = obj.content[:100]
            if len(obj.content) > 100:
                preview += '...'
            return preview
        return ''
    content_preview.short_description = 'Content Preview'

    def has_tool_calls(self, obj):
        """Show if message has associated tool calls"""
        if obj.tool_calls:
            return '✓'
        return '✗'
    has_tool_calls.short_description = 'Tool Calls'
    has_tool_calls.admin_order_field = 'tool_calls'

    def tool_calls_display(self, obj):
        """Display tool calls in an expandable format"""
        if not obj.tool_calls:
            return 'No tool calls'

        from django.utils.html import format_html
        import json

        html_parts = []
        for i, tool_call in enumerate(obj.tool_calls):
            tool_name = tool_call.get('tool_name', 'Unknown')
            parameters = tool_call.get('parameters', {})
            result = tool_call.get('result', '')
            timestamp = tool_call.get('timestamp', 'Unknown')

            # Format parameters as pretty JSON
            # Escape curly braces for format_html by doubling them
            params_json = json.dumps(parameters, indent=2).replace('{', '{{').replace('}', '}}')

            # Truncate result if too long (show first 500 chars)
            result_preview = result[:500]
            result_full = result
            if len(result) > 500:
                result_preview += '... (truncated)'

            # Create expandable section with <details> tag
            html = f"""
            <div style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #007bff; border-radius: 4px;">
                <details>
                    <summary style="cursor: pointer; font-weight: bold; font-size: 14px; color: #007bff;">
                        🔧 Tool Call #{i+1}: {tool_name}
                    </summary>
                    <div style="margin-top: 15px; padding: 10px; background-color: white; border-radius: 4px;">
                        <p><strong>⏰ Timestamp:</strong> {timestamp}</p>
                        <p><strong>📥 Parameters:</strong></p>
                        <pre style="background-color: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px;">{params_json}</pre>
                        <p><strong>📤 Result:</strong></p>
                        <pre style="background-color: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; max-height: 400px; font-size: 12px; white-space: pre-wrap;">{result_full}</pre>
                    </div>
                </details>
            </div>
            """
            html_parts.append(html)

        return format_html(''.join(html_parts))
    tool_calls_display.short_description = 'Tool Call Details'

    def has_add_permission(self, request):
        """Prevent manual message creation through admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent message deletion through admin (for data integrity)"""
        return False
