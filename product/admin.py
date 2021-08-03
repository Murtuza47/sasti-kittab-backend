from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Order_Item)
admin.site.register(Review)
admin.site.register(Shipping_Address)
