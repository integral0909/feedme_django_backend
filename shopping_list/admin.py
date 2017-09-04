from django.contrib import admin
from shopping_list.models import ShoppingList, CustomItem, Item


class ItemInline(admin.TabularInline):
    model = Item


class CustomItemInline(admin.TabularInline):
    model = CustomItem


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'items_count', 'custom_items_count', 'created')
    inlines = (CustomItemInline, ItemInline)

    def items_count(self, obj):
        return obj.items.count()

    def custom_items_count(self, obj):
        return obj.custom_items.count()


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ticked')
