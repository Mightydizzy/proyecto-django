from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import F


# Usuario con RUT
class CustomUser(AbstractUser):
    rut = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return f"{self.username} ({self.rut})"


# Cuentas bancarias
class BankAccount(models.Model):
    class AccountType(models.TextChoices):
        CHECKING = "CC", "Cuenta Corriente"
        SAVINGS = "CA", "Caja de Ahorro"
        SALARY = "CS", "Cuenta Sueldo"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accounts"
    )
    account_number = models.CharField(
        max_length=20,
        unique=True
    )
    account_type = models.CharField(
        max_length=2,
        choices=AccountType.choices
    )
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account_number} - {self.get_account_type_display()} ({self.owner.username}) ${self.balance}"



# Contactos
class Contact(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts"
    )
    alias = models.CharField(max_length=100)
    linked_account = models.ForeignKey(   # 👈 nuevo campo
        "BankAccount",
        on_delete=models.CASCADE,
        related_name="incoming_contacts"
    )

    class Meta:
        ordering = ["alias"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "alias"], name="unique_contact_alias_per_owner"),
            models.UniqueConstraint(fields=["owner", "linked_account"], name="unique_account_per_owner"),
        ]

    def __str__(self):
        return f"{self.alias} ({self.linked_account.account_number})"


# Transferencias
class Transfer(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pendiente", "Pendiente"
        COMPLETED = "Completada", "Completada"
        FAILED = "Fallida", "Fallida"

    origin_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="transfers_out")
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT, related_name="transfers_in")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"${self.amount} a {self.contact.alias} desde {self.origin_account.name} [{self.status}]"


# Movimientos
class Transaction(models.Model):
    class Type(models.TextChoices):
        INCOME = "Ingreso", "Ingreso"
        EXPENSE = "Egreso", "Egreso"

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="movements")
    type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        sign = "-" if self.type == self.Type.EXPENSE else "+"
        return f"{sign}${self.amount} {self.description}"


# Lógica de negocio
def perform_transfer(*, origin_account: BankAccount, contact: Contact, amount: Decimal, note: str = "") -> Transfer:
    if amount <= 0:
        raise ValidationError("El monto debe ser mayor a 0.")

    with db_transaction.atomic():
        acc = BankAccount.objects.select_for_update().get(pk=origin_account.pk)
        if acc.balance < amount:
            raise ValidationError("Saldo insuficiente para realizar la transferencia.")

        acc.balance = F("balance") - amount
        acc.save(update_fields=["balance"])

        Transaction.objects.create(
            account=acc,
            type=Transaction.Type.EXPENSE,
            amount=amount,
            description=f"Transferencia a {contact.alias} ({contact.linked_account.owner.username})",
        )

        dest_acc = BankAccount.objects.select_for_update().get(pk=contact.linked_account.pk)
        dest_acc.balance = F("balance") + amount
        dest_acc.save(update_fields=["balance"])

        Transaction.objects.create(
            account=dest_acc,
            type=Transaction.Type.INCOME,
            amount=amount,
            description=f"Transferencia recibida de {acc.owner.username}",
        )

        transfer = Transfer.objects.create(
            origin_account=acc,
            contact=contact,
            amount=amount,
            note=note,
            status=Transfer.Status.COMPLETED,
        )

        return transfer
