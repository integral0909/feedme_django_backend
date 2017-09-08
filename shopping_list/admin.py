from django.contrib import admin
from django import forms
from shopping_list.models import ShoppingList, CustomItem, Item


class ItemInline(admin.TabularInline):
    model = Item
    readonly_fields = ('recipe', 'ingredient', 'ticked')
    extra = 0
    can_delete = False


class CustomItemInline(admin.TabularInline):
    model = CustomItem
    readonly_fields = ('content', 'ticked')
    extra = 0
    can_delete = False


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'items_count', 'custom_items_count', 'created')
    readonly_fields = ('created', 'items_count', 'custom_items_count')
    inlines = (CustomItemInline, ItemInline)

    def items_count(self, obj):
        return obj.items.count()

    def custom_items_count(self, obj):
        return obj.custom_items.count()


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ticked')
