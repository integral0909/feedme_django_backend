from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    recipe = models.ForeignKey('main.Recipe')
    shopping_list = models.ForeignKey('ShoppingList', on_delete=models.CASCADE,
                                       related_name='items')
    ingredient = models.TextField(default='')
    ticked = models.BooleanField(default=False)

    def __str__(self):
        return self.ingredient


class CustomItem(models.Model):
    shopping_list = models.ForeignKey('ShoppingList', on_delete=models.CASCADE,
                                       related_name='custom_items')
    content = models.TextField(default='')
    ticked = models.BooleanField(default=False)

    def __str__(self):
        return self.content


class ShoppingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_lists')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.created)
