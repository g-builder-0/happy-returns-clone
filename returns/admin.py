from django.contrib import admin
from .models import Merchant, Consumer, Return, ReturnItem, ReturnLabel, ReturnBarLocation, ItemConditionAssessment, \
    RefundTransaction

admin.site.register(Merchant)
admin.site.register(Consumer)
admin.site.register(Return)
admin.site.register(ReturnItem)
admin.site.register(ReturnLabel)
admin.site.register(ReturnBarLocation)
admin.site.register(ItemConditionAssessment)
admin.site.register(RefundTransaction)