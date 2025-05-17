from django.contrib import admin
from .models import Product, Category, Order, OrderProduct, Wishlist, WishlistProduct

# Register your models here.

admin.site.register(Product)
admin.site.register(Category)


class OrderItemInLine(admin.TabularInline):
    model = OrderProduct
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'total', 'date', 'status']
    inlines = [OrderItemInLine]


class WishlistItemInLine(admin.TabularInline):
    model = WishlistProduct
    raw_id_fields = ['product']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user']
    inlines = [WishlistItemInLine]
