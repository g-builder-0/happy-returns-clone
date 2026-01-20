from django.contrib import admin
from .models import Merchant, Consumer, Return, ReturnItem

admin.site.register(Merchant)
admin.site.register(Consumer)
admin.site.register(Return)
admin.site.register(ReturnItem)