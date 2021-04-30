from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Class)
admin.site.register(Year)
admin.site.register(Student)
admin.site.register(DueAmount)
admin.site.register(PaidAmount)
admin.site.register(YearPaidAmount)
