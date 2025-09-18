# Em app_analise/admin.py

from django.contrib import admin
# Importe TODOS os seus modelos
from .models import Liga, Time, Jogo, AnaliseTime, Banca, Aposta

@admin.register(Liga)
class LigaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)

@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'liga')
    list_filter = ('liga',)
    search_fields = ('nome',)

@admin.register(AnaliseTime)
class AnaliseTimeAdmin(admin.ModelAdmin):
    list_display = ('time', 'liga', 'jogos', 'jogos_casa', 'jogos_fora')
    list_filter = ('liga',)
    search_fields = ('time__nome',)

@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    list_display = ('id', 'data', 'time_casa', 'time_fora', 'liga')
    list_filter = ('liga', 'data')
    search_fields = ('time_casa__nome', 'time_fora__nome')

# --- ADICIONADO AGORA ---

@admin.register(Banca)
class BancaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valor_inicial', 'ativa')
    list_filter = ('ativa',)

@admin.register(Aposta)
class ApostaAdmin(admin.ModelAdmin):
    list_display = ('evento', 'banca', 'valor_apostado', 'odd', 'resultado', 'retorno', 'data')
    list_filter = ('banca', 'resultado', 'data')
    search_fields = ('evento', 'mercado')
    ordering = ['-data'] 