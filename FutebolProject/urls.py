# Path: FutebolProject/urls.py (VERSÃO CORRIGIDA)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esta linha diz ao Django para usar o arquivo urls.py da sua app_analise
    path('', include(('app_analise.urls', 'app_analise'))),
    path('accounts/', include('django.contrib.auth.urls')),
]