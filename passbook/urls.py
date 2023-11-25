"""passbook URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("register.urls")),
    path("record/", include("record.urls")),
    path("monthly_report/", include("monthly_report.urls")),
    path("check_record/", include("check_record.urls")),
    path("control/", include("control.urls")),
    path("budget/", include("budget.urls")),
    path("payment/", include("payment.urls")),
    path("kurasel/", include("kurasel_translator.urls")),
    path("explanation/", include("explanation.urls")),
]

if settings.DEBUG:
    # for django-debug-toolbar
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
