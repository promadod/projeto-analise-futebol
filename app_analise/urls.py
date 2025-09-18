from django.urls import path
from . import views

# Define o "apelido" (namespace) para este conjunto de URLs.
app_name = 'app_analise'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/banca/<int:banca_id>/', views.home, name='home_banca'),
    path('dashboard/banca/<int:banca_id>/<int:year>/<int:month>/', views.home,name='home_mensal'),
    path('analise/', views.painel_de_analise, name='dashboard'),
    path('api/comparar-times/', views.comparar_times_api, name='comparar_times_api'),
    path('ranking/', views.ranking_view, name='ranking_view'),
    path('rankings/', views.rankings_page, name='rankings_page'),
    path('api/get-team-stats/<int:time_id>/', views.get_team_stats, name='get_team_stats'),
    path('api/get-times/<int:liga_id>/', views.get_times_for_liga, name='get_times_for_liga'),
    path('cadastrar-liga/', views.cadastrar_liga, name='cadastrar_liga'),
    path('cadastrar-time/', views.cadastrar_time, name='cadastrar_time'),
    path('cadastrar-jogo/', views.cadastrar_jogo, name='cadastrar_jogo'),
    path('gestao/bancas/', views.gerenciar_bancas_view, name='gerenciar_bancas'),
    path('gestao/bancas/nova/', views.criar_banca_view, name='criar_banca'),
    path('gestao/bancas/<int:banca_id>/editar/', views.editar_banca_view, name='editar_banca'),
    path('gestao/bancas/<int:banca_id>/deletar/', views.deletar_banca_view, name='deletar_banca'),
    path('gestao/dashboard/', views.dashboard_apostas_view, name='dashboard_apostas'),
    path('gestao/lancamento/', views.lancamento_aposta_view, name='lancamento_aposta'),
    path('gestao/aposta/<int:aposta_id>/editar/', views.editar_aposta_view, name='editar_aposta'),
    path('gestao/aposta/<int:aposta_id>/deletar/', views.deletar_aposta_view, name='deletar_aposta'),
    path('api/ligas/', views.listar_ligas_api, name='api_listar_ligas'),
    path('api/rankings/', views.gerar_destaques_da_liga_api, name='api_buscar_rankings'),
    path('ligas/adicionar/', views.adicionar_liga, name='adicionar_liga'),
    path('gerenciar/', views.gerenciar_ligas, name='gerenciar_ligas'),
    path('ligas/<int:liga_id>/adicionar-time/', views.adicionar_time, name='adicionar_time'),
    path('jogos/adicionar/', views.adicionar_jogo, name='adicionar_jogo'),
    path('api/get-times/<int:liga_id>/', views.get_times_for_liga, name='get_times_for_liga'),
    path('ligas/<int:liga_id>/jogos/', views.ver_jogos_liga, name='ver_jogos_liga'),
    path('api/get-custom-stats/<int:time_a_id>/<int:time_b_id>/', views.get_custom_stats_api, name='get_custom_stats_api'),
    path('teste-card/<int:time_a_id>/<int:time_b_id>/', views.teste_card_view, name='teste_card'),
]

