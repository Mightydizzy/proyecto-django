"""
URL configuration for aceitubank project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from banco import views as banco_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Autenticación
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", banco_views.signup, name="signup"),

    # Home (página pública de inicio)
    path("", banco_views.home, name="home"),

    # Dashboard (después de login)
    path("dashboard/", banco_views.dashboard, name="dashboard"),

    # Cuentas
    path("accounts/", banco_views.AccountListView.as_view(), name="accounts_list"),

    # Contactos
    path("contacts/", banco_views.ContactListView.as_view(), name="contacts_list"),
    path("contacts/create/", banco_views.ContactCreateView.as_view(), name="contact_create"),
    path("contacts/<int:pk>/edit/", banco_views.ContactUpdateView.as_view(), name="contact_edit"),
    path("contacts/<int:pk>/delete/", banco_views.ContactDeleteView.as_view(), name="contact_delete"),

    # Transferencias
    path("transfers/create/", banco_views.TransferCreateView.as_view(), name="transfer_create"),

    # Movimientos
    path("transactions/", banco_views.TransactionListView.as_view(), name="transactions_list"),
]

