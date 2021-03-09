from django.contrib import admin

# Register your models here.
from alias.models import (
    Slug,
    TestModel,
    Alias)
from django.contrib import admin

admin.site.register(Slug)
admin.site.register(TestModel)
admin.site.register(Alias)
