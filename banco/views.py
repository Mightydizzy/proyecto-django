from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .forms import SignUpForm, ContactForm, TransferForm
from .models import BankAccount, Transaction, Contact, Transfer, perform_transfer


# Vista pública home
def home(request):
    return render(request, "home.html")


# Vista de registro de usuarios
def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registro exitoso, ¡bienvenido!")
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


# Vista de cuentas
class AccountListView(LoginRequiredMixin, ListView):
    model = BankAccount
    template_name = "accounts.html"
    context_object_name = "accounts"

    def get_queryset(self):
        return BankAccount.objects.filter(owner=self.request.user)


# Lista de contactos
class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = "contacts_list.html"
    context_object_name = "contacts"

    def get_queryset(self):
        return Contact.objects.filter(owner=self.request.user)


# Crear contacto
class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = "contact_form.html"
    success_url = reverse_lazy("contacts_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


# Editar contacto
class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = "contact_form.html"
    success_url = reverse_lazy("contacts_list")

    def get_queryset(self):
        return Contact.objects.filter(owner=self.request.user)


# Eliminar contacto
class ContactDeleteView(LoginRequiredMixin, DeleteView):
    model = Contact
    template_name = "contact_confirm_delete.html"
    success_url = reverse_lazy("contacts_list")

    def get_queryset(self):
        return Contact.objects.filter(owner=self.request.user)


# Crear transferencia (usando perform_transfer)
class TransferCreateView(LoginRequiredMixin, CreateView):
    model = Transfer
    form_class = TransferForm
    template_name = "transfer_form.html"
    success_url = reverse_lazy("transactions_list")

    def get_queryset(self):
        return self.model.objects.filter(origin_account__owner=self.request.user)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["origin_account"].queryset = form.fields["origin_account"].queryset.filter(owner=self.request.user)
        form.fields["contact"].queryset = form.fields["contact"].queryset.filter(owner=self.request.user)
        return form

    def form_valid(self, form):
        origin_account = form.cleaned_data["origin_account"]
        contact = form.cleaned_data["contact"]
        amount = form.cleaned_data["amount"]
        note = form.cleaned_data.get("note", "")

        try:
            perform_transfer(
                origin_account=origin_account,
                contact=contact,
                amount=amount,
                note=note,
            )
            messages.success(self.request, "✅ Transferencia realizada con éxito.")
        except Exception as e:
            messages.error(self.request, f"❌ Error en la transferencia: {e}")
            return self.form_invalid(form)

        return redirect(self.success_url)


# Listar transacciones
class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions.html"
    context_object_name = "movements"
    paginate_by = 10

    def get_queryset(self):
        return Transaction.objects.filter(account__owner=self.request.user).order_by("-date")


# Vista privada (dashboard)
@login_required
def dashboard(request):
    accounts = BankAccount.objects.filter(owner=request.user)
    movements = Transaction.objects.filter(account__owner=request.user)

    paginator = Paginator(movements, 10)
    page = request.GET.get("page")
    movements_page = paginator.get_page(page)

    return render(
        request,
        "dashboard.html",
        {"accounts": accounts, "movements": movements_page}
    )
