from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

# Account model configuration for admin panel
class AccountAdmin(UserAdmin):
    list_display       = ('email', 'first_name', 'last_name', 'username', 'date_joined', 'last_login', 'is_active')
    list_display_links = ('email', 'username')
    readonly_fields    = ('date_joined', 'last_login')

    ordering          = ('-date_joined',) # desc
    filter_horizontal = ()
    list_filter       = ()
    fieldsets = () # Make password read-only

# Register your models here.
admin.site.register(Account, AccountAdmin)
