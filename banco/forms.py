from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Contact, Transfer, BankAccount



class SignUpForm(UserCreationForm):
    rut = forms.CharField(
        max_length=12,
        help_text="Ingresa tu RUT sin puntos y con guión opcional"
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "rut", "email")


class ContactForm(forms.ModelForm):
    rut = forms.CharField(
        max_length=12,
        label="RUT del destinatario",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    account_number = forms.CharField(
        max_length=20,
        label="Número de cuenta",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Contact
        fields = ["alias", "rut", "account_number"]
        widgets = {
            "alias": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        rut = cleaned_data.get("rut")
        account_number = cleaned_data.get("account_number")

        if rut and account_number:
            try:
                user = CustomUser.objects.get(rut=rut)
            except CustomUser.DoesNotExist:
                raise forms.ValidationError("El rut o el número de usuario no coinciden.")

            try:
                account = BankAccount.objects.get(owner=user, account_number=account_number)
            except BankAccount.DoesNotExist:
                raise forms.ValidationError("El rut o el número de usuario no coinciden.")

            cleaned_data["linked_account"] = account

        return cleaned_data

    def save(self, commit=True):
        contact = super().save(commit=False)
        contact.linked_account = self.cleaned_data["linked_account"]
        if commit:
            contact.save()
        return contact


class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = ["origin_account", "contact", "amount", "note"]
        widgets = {
            "origin_account": forms.Select(attrs={"class": "form-select"}),
            "contact": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ej: 50000"}),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Ej: Almuerzo."
            }),
        }
