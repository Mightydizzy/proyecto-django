from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, BankAccount, Contact, Transfer, Transaction

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Datos adicionales", {"fields": ("rut",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("rut",)}),
    )
    list_display = ("username", "rut", "email", "is_staff")
    search_fields = ("username", "email", "rut")


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "account_type", "owner", "balance", "created_at")

    def save_model(self, request, obj, form, change):
        if not obj.account_number:
            base = obj.owner.rut.replace(".", "").replace("-", "")
            count = BankAccount.objects.filter(owner=obj.owner).count() + 1
            obj.account_number = f"{base}{count:02d}"
        super().save_model(request, obj, form, change)



@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("alias", "get_account_number", "get_bank_owner")

    def get_account_number(self, obj):
        return obj.linked_account.account_number
    get_account_number.short_description = "Número de cuenta"

    def get_bank_owner(self, obj):
        return obj.linked_account.owner.username
    get_bank_owner.short_description = "Propietario"


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ("origin_account", "contact", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("contact__alias", "origin_account__name")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("account", "type", "amount", "date", "description")
    list_filter = ("type", "date")
    search_fields = ("account__name", "description")
