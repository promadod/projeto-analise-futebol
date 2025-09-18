from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Jogo, AnaliseTime, Liga, Time, Aposta, Configuracao, Banca
from .forms import LigaForm, TimeForm, JogoForm, ApostaForm, BancaForm
import unicodedata
from datetime import datetime
import pandas as pd
from django.db.models import Sum, Count, Avg, Q, Case, When, DecimalField 
from django.db.models.functions import TruncMonth, Coalesce 
import json 
from django.utils.safestring import mark_safe
from decimal import Decimal
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.contrib import messages
import calendar
from datetime import date
from django.db.models import Sum
from django.db import models 
from decimal import Decimal
from django.contrib.auth.decorators import login_required
import json
from django.utils.safestring import mark_safe



def remover_acentos(texto):
    #...
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def recalcular_analise_completa():
    #...
    print("Recalculo da análise concluído.")


def painel_de_analise(request):
    todos_os_times = Time.objects.select_related('liga').order_by('nome')
    time_a_id = request.GET.get('time_a')
    time_b_id = request.GET.get('time_b')

    context = {
        'todos_os_times': todos_os_times,
        'time_a_selecionado_id': time_a_id,
        'time_b_selecionado_id': time_b_id,
        'resultados': None
    }

    if time_a_id and time_b_id:
        try:
            analise_a = AnaliseTime.objects.get(time_id=time_a_id)
            analise_b = AnaliseTime.objects.get(time_id=time_b_id)
            
            def calcular_medias_sofridas(time_obj, local):
                medias = {}
                jogos = Jogo.objects.filter(time_casa=time_obj.time) if local == 'casa' else Jogo.objects.filter(time_fora=time_obj.time)
                jogos_count = time_obj.jogos_casa if local == 'casa' else time_obj.jogos_fora
                
                campos_map = {
                    'gols': {'casa': 'placar_fora', 'fora': 'placar_casa'},
                    'finalizacoes': {'casa': 'finalizacao_fora', 'fora': 'finalizacao_casa'},
                    'chutes': {'casa': 'chutes_no_gol_fora', 'fora': 'chutes_no_gol_casa'},
                    'escanteios': {'casa': 'escanteios_fora', 'fora': 'escanteios_casa'},
                    'cartoes': {'casa': 'cartoes_amarelos_fora', 'fora': 'cartoes_amarelos_casa'}
                }

                for stat_name, field_map in campos_map.items():
                    base_field = field_map[local]
                    total_1t = jogos.aggregate(soma=Sum(f'{base_field}_1t'))['soma'] or 0
                    total_2t = jogos.aggregate(soma=Sum(f'{base_field}_2t'))['soma'] or 0
                    
                    medias[f'{stat_name}_1t'] = total_1t / jogos_count if jogos_count > 0 else 0
                    medias[f'{stat_name}_2t'] = total_2t / jogos_count if jogos_count > 0 else 0
                    medias[f'{stat_name}_total'] = medias[f'{stat_name}_1t'] + medias[f'{stat_name}_2t']
                return medias

            medias_sofridas_a = calcular_medias_sofridas(analise_a, 'casa')
            medias_sofridas_b = calcular_medias_sofridas(analise_b, 'fora')
            
            # --- SUA LÓGICA ORIGINAL PARA O JOGO COMPLETO ---
            xg_a = (analise_a.media_placar_casa_total + medias_sofridas_b['gols_total']) / 2
            xg_b = (analise_b.media_placar_fora_total + medias_sofridas_a['gols_total']) / 2
            xg_total_xg = xg_a + xg_b
            probabilidades_xg = {
                'over_0_5_gols': min(98, int(xg_total_xg * 40)), 'over_1_5_gols': min(95, int(xg_total_xg * 30)),
                'over_2_5_gols': min(95, int(xg_total_xg * 22)), 'btts_sim': min(95, int((xg_a / (xg_total_xg + 0.01)) * (xg_b / (xg_total_xg + 0.01)) * 200))
            }
            potencial_gols_4f = (analise_a.media_placar_casa_total + medias_sofridas_a['gols_total'] + analise_b.media_placar_fora_total + medias_sofridas_b['gols_total'])
            potencial_btts = analise_a.media_placar_casa_total + analise_b.media_placar_fora_total
            probabilidades_4f = {
                'over_0_5': min(98, int(potencial_gols_4f * 25)), 'over_1_5': min(95, int(potencial_gols_4f * 20)),
                'over_2_5': min(95, int(potencial_gols_4f * 15)), 'btts_sim': min(95, int(potencial_btts * 35))
            }
            total_finalizacoes = analise_a.media_finalizacao_casa_total + analise_b.media_finalizacao_fora_total
            total_escanteios = analise_a.media_escanteios_casa_total + analise_b.media_escanteios_fora_total
            total_chutes = analise_a.media_chutes_no_gol_casa_total + analise_b.media_chutes_no_gol_fora_total
            total_cartoes = analise_a.media_cartoes_amarelos_casa_total + analise_b.media_cartoes_amarelos_fora_total
            probabilidades_mercados_simples = {
                'over_22_5_finalizacoes': min(95, int(total_finalizacoes * 3)), 'over_24_5_finalizacoes': min(95, int(total_finalizacoes * 2.5)),
                'over_8_5_escanteios': min(95, int(total_escanteios * 7)), 'over_9_5_escanteios': min(95, int(total_escanteios * 6)),
                'over_7_5_chutes': min(95, int(total_chutes * 9)), 'over_8_5_chutes': min(95, int(total_chutes * 8)),
                'over_3_5_cartoes': min(95, int(total_cartoes * 18)), 'over_4_5_cartoes': min(95, int(total_cartoes * 15)),
            }

            # --- NOVA LÓGICA PARA PROBABILIDADES POR TEMPO ---
            potencial_gols_1T = (analise_a.media_placar_casa_1t + medias_sofridas_a['gols_1t'] + analise_b.media_placar_fora_1t + medias_sofridas_b['gols_1t'])
            potencial_gols_2T = (analise_a.media_placar_casa_2t + medias_sofridas_a['gols_2t'] + analise_b.media_placar_fora_2t + medias_sofridas_b['gols_2t'])
            prob_gols_1T = {'over_0_5': min(98, int(potencial_gols_1T * 55)), 'over_1_5': min(95, int(potencial_gols_1T * 20))}
            prob_gols_2T = {'over_0_5': min(98, int(potencial_gols_2T * 50)), 'over_1_5': min(95, int(potencial_gols_2T * 25))}
            total_finalizacoes_1T = analise_a.media_finalizacao_casa_1t + analise_b.media_finalizacao_fora_1t
            total_finalizacoes_2T = analise_a.media_finalizacao_casa_2t + analise_b.media_finalizacao_fora_2t
            prob_finalizacoes_1T = {'over_4_5': min(95, int(total_finalizacoes_1T * 8)), 'over_5_5': min(95, int(total_finalizacoes_1T * 6))}
            prob_finalizacoes_2T = {'over_5_5': min(95, int(total_finalizacoes_2T * 7)), 'over_6_5': min(95, int(total_finalizacoes_2T * 5))}
            total_chutes_1T = analise_a.media_chutes_no_gol_casa_1t + analise_b.media_chutes_no_gol_fora_1t
            total_chutes_2T = analise_a.media_chutes_no_gol_casa_2t + analise_b.media_chutes_no_gol_fora_2t
            prob_chutes_1T = {'over_1_5': min(95, int(total_chutes_1T * 25)), 'over_2_5': min(95, int(total_chutes_1T * 15))}
            prob_chutes_2T = {'over_2_5': min(95, int(total_chutes_2T * 20)), 'over_3_5': min(95, int(total_chutes_2T * 12))}
            total_escanteios_1T = analise_a.media_escanteios_casa_1t + analise_b.media_escanteios_fora_1t
            total_escanteios_2T = analise_a.media_escanteios_casa_2t + analise_b.media_escanteios_fora_2t
            prob_escanteios_1T = {'over_3_5': min(95, int(total_escanteios_1T * 12)), 'over_4_5': min(95, int(total_escanteios_1T * 10))}
            prob_escanteios_2T = {'over_4_5': min(95, int(total_escanteios_2T * 10)), 'over_5_5': min(95, int(total_escanteios_2T * 8))}
            total_cartoes_1T = analise_a.media_cartoes_amarelos_casa_1t + analise_b.media_cartoes_amarelos_fora_1t
            total_cartoes_2T = analise_a.media_cartoes_amarelos_casa_2t + analise_b.media_cartoes_amarelos_fora_2t
            prob_cartoes_1T = {'over_1_5': min(95, int(total_cartoes_1T * 30)), 'over_2_5': min(95, int(total_cartoes_1T * 18))}
            prob_cartoes_2T = {'over_1_5': min(95, int(total_cartoes_2T * 28)), 'over_2_5': min(95, int(total_cartoes_2T * 15))}

            stats_data = {
                'time_a': {
                    'gols_marcados_1t': analise_a.media_placar_casa_1t,
                    'gols_marcados_2t': analise_a.media_placar_casa_2t,
                    'gols_sofridos_1t': medias_sofridas_a.get('gols_1t', 0),
                    'gols_sofridos_2t': medias_sofridas_a.get('gols_2t', 0),
                    'finalizacoes_marcados_1t': analise_a.media_finalizacao_casa_1t,
                    'finalizacoes_marcados_2t': analise_a.media_finalizacao_casa_2t,
                    'finalizacoes_sofridos_1t': medias_sofridas_a.get('finalizacoes_1t', 0),
                    'finalizacoes_sofridos_2t': medias_sofridas_a.get('finalizacoes_2t', 0),
                    'chutes_marcados_1t': analise_a.media_chutes_no_gol_casa_1t,
                    'chutes_marcados_2t': analise_a.media_chutes_no_gol_casa_2t,
                    'chutes_sofridos_1t': medias_sofridas_a.get('chutes_1t', 0),
                    'chutes_sofridos_2t': medias_sofridas_a.get('chutes_2t', 0),
                    'escanteios_marcados_1t': analise_a.media_escanteios_casa_1t,
                    'escanteios_marcados_2t': analise_a.media_escanteios_casa_2t,
                    'escanteios_sofridos_1t': medias_sofridas_a.get('escanteios_1t', 0),
                    'escanteios_sofridos_2t': medias_sofridas_a.get('escanteios_2t', 0),
                    'cartoes_marcados_1t': analise_a.media_cartoes_amarelos_casa_1t,
                    'cartoes_marcados_2t': analise_a.media_cartoes_amarelos_casa_2t,
                    'cartoes_sofridos_1t': medias_sofridas_a.get('cartoes_1t', 0),
                    'cartoes_sofridos_2t': medias_sofridas_a.get('cartoes_2t', 0),
                },
                'time_b': {
                    'gols_marcados_1t': analise_b.media_placar_fora_1t,
                    'gols_marcados_2t': analise_b.media_placar_fora_2t,
                    'gols_sofridos_1t': medias_sofridas_b.get('gols_1t', 0),
                    'gols_sofridos_2t': medias_sofridas_b.get('gols_2t', 0),
                    'finalizacoes_marcados_1t': analise_b.media_finalizacao_fora_1t,
                    'finalizacoes_marcados_2t': analise_b.media_finalizacao_fora_2t,
                    'finalizacoes_sofridos_1t': medias_sofridas_b.get('finalizacoes_1t', 0),
                    'finalizacoes_sofridos_2t': medias_sofridas_b.get('finalizacoes_2t', 0),
                    'chutes_marcados_1t': analise_b.media_chutes_no_gol_fora_1t,
                    'chutes_marcados_2t': analise_b.media_chutes_no_gol_fora_2t,
                    'chutes_sofridos_1t': medias_sofridas_b.get('chutes_1t', 0),
                    'chutes_sofridos_2t': medias_sofridas_b.get('chutes_2t', 0),
                    'escanteios_marcados_1t': analise_b.media_escanteios_fora_1t,
                    'escanteios_marcados_2t': analise_b.media_escanteios_fora_2t,
                    'escanteios_sofridos_1t': medias_sofridas_b.get('escanteios_1t', 0),
                    'escanteios_sofridos_2t': medias_sofridas_b.get('escanteios_2t', 0),
                    'cartoes_marcados_1t': analise_b.media_cartoes_amarelos_fora_1t,
                    'cartoes_marcados_2t': analise_b.media_cartoes_amarelos_fora_2t,
                    'cartoes_sofridos_1t': medias_sofridas_b.get('cartoes_1t', 0),
                    'cartoes_sofridos_2t': medias_sofridas_b.get('cartoes_2t', 0),
                }
            }
            stats_json = mark_safe(json.dumps(stats_data))
            
            # --- JUNÇÃO DE TODOS OS RESULTADOS ---
            resultados_finais = {
                'time_a': analise_a, 'time_b': analise_b,
                'medias_sofridas_a': medias_sofridas_a, 'medias_sofridas_b': medias_sofridas_b,
                'probabilidades_xg': probabilidades_xg,
                'probabilidades_4f': probabilidades_4f,
                'probabilidades_mercados_simples': probabilidades_mercados_simples,
                'prob_gols_1T': prob_gols_1T, 'prob_gols_2T': prob_gols_2T,
                'prob_finalizacoes_1T': prob_finalizacoes_1T, 'prob_finalizacoes_2T': prob_finalizacoes_2T,
                'prob_chutes_1T': prob_chutes_1T, 'prob_chutes_2T': prob_chutes_2T,
                'prob_escanteios_1T': prob_escanteios_1T, 'prob_escanteios_2T': prob_escanteios_2T,
                'prob_cartoes_1T': prob_cartoes_1T, 'prob_cartoes_2T': prob_cartoes_2T,
            }
            context['resultados'] = resultados_finais

        except AnaliseTime.DoesNotExist:
            context['erro'] = "Um ou ambos os times selecionados não possuem dados de análise."

    return render(request, 'app_analise/painel.html', context)


def cadastrar_liga(request):
    if request.method == 'POST':
        form = LigaForm(request.POST)
        if form.is_valid():
            form.save()
            # CORREÇÃO: Usando o novo nome da URL
            return redirect('app_analise:dashboard')
    else:
        form = LigaForm()
    return render(request, 'app_analise/cadastrar_generico.html', {'form': form, 'titulo': 'Cadastrar Nova Liga'})

def cadastrar_time(request):
    if request.method == 'POST':
        form = TimeForm(request.POST)
        if form.is_valid():
            form.save()
            # CORREÇÃO: Usando o novo nome da URL
            return redirect('app_analise:dashboard')
    else:
        form = TimeForm()
    return render(request, 'app_analise/cadastrar_generico.html', {'form': form, 'titulo': 'Cadastrar Novo Time'})

def cadastrar_jogo(request):
    if request.method == 'POST':
        form = JogoForm(request.POST)
        if form.is_valid():
            # ... (sua lógica de salvar o jogo)
            form.save() # Simplificando, assumindo que form.save() funciona
            recalcular_analise_completa()
            # CORREÇÃO: Usando o novo nome da URL
            return redirect('app_analise:dashboard')
        else:
            liga_id = request.POST.get('liga')
            if liga_id:
                times = Time.objects.filter(liga_id=liga_id).order_by('nome')
                form.fields['time_casa'].queryset = times
                form.fields['time_fora'].queryset = times
    else:
        form = JogoForm()
    return render(request, 'app_analise/cadastrar_jogo.html', {'form': form})


def carregar_times(request):
    # ... (sua view carregar_times continua aqui, sem alterações) ...
    liga_id = request.GET.get('liga_id')
    times = Time.objects.filter(liga_id=liga_id).order_by('nome')
    return JsonResponse(list(times.values('id', 'nome')), safe=False)


def ranking_view(request):
    todas_as_ligas = Liga.objects.all().order_by('nome')
    
    # =========== CORREÇÃO PRINCIPAL AQUI ===========
    # A lista de opções de ranking agora está completa, igual à do dashboard
    opcoes_ranking = {
        'Nome do Time (A-Z)': 'time__nome',
        'Gols (Geral 1T)': '-media_placar_geral_1t', 'Gols (Geral 2T)': '-media_placar_geral_2t', 'Gols (Geral Total)': '-media_placar_geral_total',
        'Finalizações (Geral 1T)': '-media_finalizacao_geral_1t', 'Finalizações (Geral 2T)': '-media_finalizacao_geral_2t', 'Finalizações (Geral Total)': '-media_finalizacao_geral_total',
        'Chutes no Gol (Geral 1T)': '-media_chutes_no_gol_geral_1t', 'Chutes no Gol (Geral 2T)': '-media_chutes_no_gol_geral_2t', 'Chutes no Gol (Geral Total)': '-media_chutes_no_gol_geral_total',
        'Escanteios (Geral 1T)': '-media_escanteios_geral_1t', 'Escanteios (Geral 2T)': '-media_escanteios_geral_2t', 'Escanteios (Geral Total)': '-media_escanteios_geral_total',
        'Cartões Amarelos (Geral 1T)': '-media_cartoes_amarelos_geral_1t', 'Cartões Amarelos (Geral 2T)': '-media_cartoes_amarelos_geral_2t', 'Cartões Amarelos (Geral Total)': '-media_cartoes_amarelos_geral_total',
    }
    # ================= FIM DA CORREÇÃO =================

    liga_selecionada_id = request.GET.get('liga')
    ordenar_por = request.GET.get('ordenar_por', '-media_placar_geral_total')
    
    analises = AnaliseTime.objects.select_related('liga', 'time').all()

    if liga_selecionada_id:
        analises = analises.filter(liga_id=liga_selecionada_id)
    
    analises = analises.order_by(ordenar_por)

    for a in analises:
        campo = ordenar_por.lstrip('-')
        a.valor_ranqueado = getattr(a, campo, 0)

    context = {
        'analises': analises,
        'ligas': todas_as_ligas,
        'opcoes_ranking': opcoes_ranking,
        'ordenar_por_selecionado': ordenar_por,
        'liga_selecionada_id': liga_selecionada_id,
    }
    return render(request, 'app_analise/ranking.html', context)

def lancamento_aposta_view(request):
    if request.method == 'POST':
        form = ApostaForm(request.POST)
        if form.is_valid():
            form.save() # O ModelForm já sabe como salvar tudo corretamente!
            messages.success(request, "Aposta lançada com sucesso!")
            return redirect('app_analise:home') 
    else:
        form = ApostaForm()

    contexto = {
        'form': form,
    }
    
    return render(request, 'app_analise/lancamento_aposta.html', contexto)



def dashboard_apostas_view(request):
    # Pega a configuração da banca inicial
    config, created = Configuracao.objects.get_or_create(id=1)
    banca_inicial = config.banca_inicial

    # --- INÍCIO DA LÓGICA DE FILTRO ---
    apostas = Aposta.objects.all()
    
    periodo = request.GET.get('periodo')
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')

    today = date.today()

    if periodo == 'hoje':
        apostas = apostas.filter(data__date=today)
    elif periodo == 'mes':
        apostas = apostas.filter(data__year=today.year, data__month=today.month)
    elif periodo == 'ano':
        apostas = apostas.filter(data__year=today.year)
    elif data_inicio_str and data_fim_str:
        # Filtra pelo intervalo de datas selecionado
        apostas = apostas.filter(data__date__range=[data_inicio_str, data_fim_str])
    
    # --- FIM DA LÓGICA DE FILTRO ---

    # Todos os cálculos agora são feitos SOBRE o queryset já filtrado
    total_apostado = apostas.aggregate(total=Sum('valor_apostado'))['total'] or Decimal('0.00')
    lucro_prejuizo_total = apostas.aggregate(total=Sum('retorno'))['total'] or Decimal('0.00')
    
    # O saldo atual é sempre calculado com base no lucro TOTAL, não apenas do período.
    lucro_total_geral = Aposta.objects.aggregate(total=Sum('retorno'))['total'] or Decimal('0.00')
    saldo_atual = Decimal(banca_inicial) + lucro_total_geral
    
    roi = (lucro_prejuizo_total / total_apostado * 100) if total_apostado > 0 else Decimal('0.00')
    
    total_apostas = apostas.count()
    greens = apostas.filter(resultado='GREEN').count()
    reds = apostas.filter(resultado='RED').count()
    taxa_acerto = (greens / (greens + reds) * 100) if (greens + reds) > 0 else 0
    odd_media_ganha = apostas.filter(resultado='GREEN').aggregate(avg_odd=Avg('odd'))['avg_odd'] or 0

    # Gráficos e tabela também usarão os dados filtrados
    apostas_ordenadas_data = apostas.order_by('data')
    datas_evolucao = []
    saldo_evolucao = []
    
    # O gráfico de evolução precisa começar com o saldo ANTERIOR ao período filtrado
    primeira_aposta_filtrada = apostas_ordenadas_data.first()
    data_inicio_grafico = primeira_aposta_filtrada.data.date() if primeira_aposta_filtrada else today

    apostas_anteriores = Aposta.objects.filter(data__date__lt=data_inicio_grafico)
    lucro_anterior = apostas_anteriores.aggregate(total=Sum('retorno'))['total'] or Decimal('0.00')
    saldo_acumulado = float(Decimal(banca_inicial) + lucro_anterior)
    
    if apostas_ordenadas_data:
        # Adiciona um ponto inicial no gráfico com o saldo antes do período
        datas_evolucao.append((primeira_aposta_filtrada.data - timedelta(days=1)).strftime('%d/%m'))
        saldo_evolucao.append(round(saldo_acumulado, 2))

    for aposta in apostas_ordenadas_data:
        saldo_acumulado += float(aposta.retorno)
        datas_evolucao.append(aposta.data.strftime('%d/%m'))
        saldo_evolucao.append(round(saldo_acumulado, 2))

    lucro_mensal = apostas.annotate(mes=TruncMonth('data')).values('mes').annotate(total=Sum('retorno')).order_by('mes')
    meses_lucro = [item['mes'].strftime('%b/%y') for item in lucro_mensal]
    valores_lucro = [round(float(item['total']), 2) for item in lucro_mensal]

    context = {
        'banca_inicial': banca_inicial,
        'saldo_atual': saldo_atual,
        'lucro_prejuizo_total': lucro_prejuizo_total,
        'roi': roi,
        'total_apostado': total_apostado,
        'taxa_acerto': taxa_acerto,
        'total_apostas': total_apostas,
        'odd_media': odd_media_ganha,
        'greens': greens,
        'reds': reds,
        'ultimas_apostas': apostas.order_by('-data'),
        
        'datas_evolucao_json': json.dumps(datas_evolucao),
        'saldo_evolucao_json': json.dumps(saldo_evolucao),
        'dados_pie_chart_json': json.dumps([greens, reds]),
        'meses_lucro_json': json.dumps(meses_lucro),
        'valores_lucro_json': json.dumps(valores_lucro),

        # Passando os valores dos filtros de volta para o template
        'periodo_selecionado': periodo,
        'data_inicio_selecionada': data_inicio_str,
        'data_fim_selecionada': data_fim_str,
    }
    
    return render(request, 'app_analise/dashboard_apostas.html', context)

def editar_aposta_view(request, aposta_id):
    aposta = get_object_or_404(Aposta, id=aposta_id)
    if request.method == 'POST':
        form = ApostaForm(request.POST, instance=aposta)
        if form.is_valid():
            form.save()
            return redirect('app_analise:dashboard_apostas')
    else:
        form = ApostaForm(instance=aposta)
    
    context = {
        'form': form,
        'titulo': 'Editar Aposta' # Título para a página
    }
    return render(request, 'app_analise/lancamento_aposta.html', context)

def deletar_aposta_view(request, aposta_id):
    aposta = get_object_or_404(Aposta, id=aposta_id)
    if request.method == 'POST':
        aposta.delete()
        return redirect('app_analise:dashboard_apostas')
    
    return render(request, 'app_analise/aposta_confirm_delete.html', {'aposta': aposta})

def gerenciar_bancas_view(request):
    bancas = Banca.objects.all().order_by('nome')
    return render(request, 'app_analise/gerenciar_bancas.html', {'bancas': bancas})

def criar_banca_view(request):
    if request.method == 'POST':
        form = BancaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('app_analise:gerenciar_bancas')
    else:
        form = BancaForm()
    return render(request, 'app_analise/banca_form.html', {'form': form, 'titulo': 'Criar Nova Banca'})

def editar_banca_view(request, banca_id):
    banca = get_object_or_404(Banca, id=banca_id)
    if request.method == 'POST':
        form = BancaForm(request.POST, instance=banca)
        if form.is_valid():
            form.save()
            return redirect('app_analise:gerenciar_bancas')
    else:
        form = BancaForm(instance=banca)
    return render(request, 'app_analise/banca_form.html', {'form': form, 'titulo': f'Editar Banca: {banca.nome}'})

def deletar_banca_view(request, banca_id):
    banca = get_object_or_404(Banca, id=banca_id)
    if request.method == 'POST':
        banca.delete()
        return redirect('app_analise:gerenciar_bancas')
    return render(request, 'app_analise/banca_confirm_delete.html', {'banca': banca})


def dashboard_apostas_view(request):
    # --- LÓGICA DE FILTRO (SEM ALTERAÇÕES) ---
    bancas = Banca.objects.filter(ativa=True)
    banca_selecionada_id = request.GET.get('banca')
    periodo = request.GET.get('periodo', 'geral')
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')

    # Query base para os filtros de data
    apostas_filtradas_por_data = Aposta.objects.all()
    today = date.today()
    if periodo == 'hoje':
        apostas_filtradas_por_data = apostas_filtradas_por_data.filter(data__date=today)
    elif periodo == 'mes':
        apostas_filtradas_por_data = apostas_filtradas_por_data.filter(data__year=today.year, data__month=today.month)
    elif periodo == 'ano':
        apostas_filtradas_por_data = apostas_filtradas_por_data.filter(data__year=today.year)
    elif periodo == 'datas' and data_inicio_str and data_fim_str:
        apostas_filtradas_por_data = apostas_filtradas_por_data.filter(data__date__range=[data_inicio_str, data_fim_str])

    # Query para os KPIs e tabela (filtra também por banca, se selecionada)
    apostas_kpi = apostas_filtradas_por_data
    banca_selecionada = None
    if banca_selecionada_id:
        apostas_kpi = apostas_kpi.filter(banca_id=banca_selecionada_id)
        banca_selecionada = Banca.objects.filter(id=banca_selecionada_id).first()

    # --- CÁLCULOS DOS KPIs (agora usam 'apostas_kpi') ---
    if banca_selecionada:
        banca_inicial = banca_selecionada.valor_inicial
        saldo_total_bancas = Banca.objects.filter(ativa=True).aggregate(total=Sum('valor_inicial'))['total'] or Decimal('0.00')
        saldo_atual_geral = saldo_total_bancas + (Aposta.objects.aggregate(total=Sum('retorno'))['total'] or Decimal('0.00'))
    else:
        banca_inicial = Banca.objects.filter(ativa=True).aggregate(total=Sum('valor_inicial'))['total'] or Decimal('0.00')
        saldo_atual_geral = banca_inicial + (Aposta.objects.aggregate(total=Sum('retorno'))['total'] or Decimal('0.00'))
        
    total_apostado = apostas_kpi.aggregate(total=Sum('valor_apostado'))['total'] or Decimal('0.00')
    lucro_prejuizo_total = apostas_kpi.aggregate(total=Sum('retorno'))['total'] or Decimal('0.00')
    saldo_atual = banca_inicial + lucro_prejuizo_total if banca_selecionada else saldo_atual_geral
    roi = (lucro_prejuizo_total / total_apostado * 100) if total_apostado > 0 else Decimal('0.00')
    total_apostas = apostas_kpi.count()
    greens = apostas_kpi.filter(resultado='GREEN').count()
    reds = apostas_kpi.filter(resultado='RED').count()
    taxa_acerto = (greens / (greens + reds) * 100) if (greens + reds) > 0 else 0
    odd_media = apostas_kpi.filter(resultado='GREEN').aggregate(avg_odd=Avg('odd'))['avg_odd'] or 0
    
    # --- GRÁFICO DE EVOLUÇÃO DA BANCA (usa 'apostas_kpi') ---
    apostas_periodo_evolucao = apostas_kpi.order_by('data')
    datas_evolucao = []
    saldo_evolucao = []

    if apostas_periodo_evolucao:
        primeira_data = apostas_periodo_evolucao.first().data
        retorno_anterior_query = Aposta.objects.filter(data__lt=primeira_data)
        if banca_selecionada:
             retorno_anterior_query = retorno_anterior_query.filter(banca=banca_selecionada)
        
        retorno_anterior = retorno_anterior_query.aggregate(total=Sum('retorno'))['total'] or Decimal('0.00')
        saldo_inicial_periodo = float(banca_inicial + retorno_anterior)
        
        datas_evolucao.append((primeira_data - timedelta(days=1)).strftime('%d/%m'))
        saldo_evolucao.append(round(saldo_inicial_periodo, 2))
        
        saldo_acumulado_grafico = saldo_inicial_periodo
        for aposta in apostas_periodo_evolucao:
            saldo_acumulado_grafico += float(aposta.retorno)
            datas_evolucao.append(aposta.data.strftime('%d/%m'))
            saldo_evolucao.append(round(saldo_acumulado_grafico, 2))

    # --- LÓGICA PARA O GRÁFICO DE MERCADO (Usa 'apostas_filtradas_por_data') ---
    # Esta seção agora é independente do filtro de banca
    desempenho_mercado_net = (
        apostas_filtradas_por_data.values('mercado')
        .annotate(total_retorno=Sum('retorno'))
        .order_by('-total_retorno')
    )
    
    desempenho_mercado_separado = (
        apostas_filtradas_por_data.values('mercado')
        .annotate(
            total_ganho=Coalesce(Sum(Case(When(resultado='GREEN', then='retorno'), output_field=DecimalField())), Decimal('0.0')),
            total_perdido=Coalesce(Sum(Case(When(resultado='RED', then='valor_apostado'), output_field=DecimalField())), Decimal('0.0')),
            # Novo campo para ordenar pelos mercados mais relevantes
            total_investido=Sum('valor_apostado')
        ).order_by('-total_investido')[:10] # Pega os 10 mercados mais apostados
    )

    mercados_labels = [item['mercado'] for item in desempenho_mercado_separado]
    mercados_ganhos = [round(float(item['total_ganho']), 2) for item in desempenho_mercado_separado]
    mercados_perdidos = [round(float(item['total_perdido']), 2) for item in desempenho_mercado_separado]
    
    # --- MONTAGEM DO CONTEXT ---
    context = {
        'bancas': bancas,
        'banca_selecionada_id': banca_selecionada_id,
        'periodo': periodo,
        'data_inicio_str': data_inicio_str,
        'data_fim_str': data_fim_str,
        'banca_inicial': banca_inicial,
        'saldo_atual': saldo_atual,
        'lucro_prejuizo_total': lucro_prejuizo_total,
        'roi': roi,
        'total_apostado': total_apostado,
        'taxa_acerto': taxa_acerto,
        'odd_media': odd_media,
        'total_apostas': total_apostas,
        'ultimas_apostas': apostas_kpi.order_by('-data'),
        'dados_pie_chart_json': json.dumps([greens, reds]),
        'datas_evolucao_json': json.dumps(datas_evolucao),
        'saldo_evolucao_json': json.dumps(saldo_evolucao),
        'mercados_labels_json': json.dumps(mercados_labels),
        'mercados_ganhos_json': json.dumps(mercados_ganhos),
        'mercados_perdidos_json': json.dumps(mercados_perdidos),
        'desempenho_mercado_data': desempenho_mercado_net,
    }
    
    return render(request, 'app_analise/dashboard_apostas.html', context)


def listar_ligas_api(request):
    """
    Busca e retorna uma lista de todas as ligas para a API.
    """
    try:
        # Usando o ORM do Django para buscar os dados de forma segura
        ligas = Liga.objects.all().order_by('nome').values('id', 'nome')
        return JsonResponse(list(ligas), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def gerar_destaques_da_liga_api(request):
    """
    Recebe o ID de uma liga e retorna uma lista com os times que são
    líderes em diversas estatísticas pré-definidas (destaques).
    VERSÃO CORRIGIDA E FINAL
    """
    liga_id = request.GET.get('liga_id')
    if not liga_id:
        return JsonResponse({'error': "O parâmetro 'liga_id' é obrigatório."}, status=400)

    # LISTA DE RANKINGS CORRIGIDA USANDO OS NOMES EXATOS DO SEU MODEL Jogo
    rankings_de_interesse = [
        # --- GOLS MARCADOS (A FAVOR) ---
        {'titulo': 'Mais Gols (1ºT em Casa)', 'campo_db': 'placar_casa_1t', 'local': 'casa'},
        {'titulo': 'Mais Gols (2ºT em Casa)', 'campo_db': 'placar_casa_2t', 'local': 'casa'},
        {'titulo': 'Mais Gols (Total em Casa)', 'campo_db': 'placar_casa_total', 'local': 'casa'},
        {'titulo': 'Mais Gols (1ºT Fora)', 'campo_db': 'placar_fora_1t', 'local': 'fora'},
        {'titulo': 'Mais Gols (2ºT Fora)', 'campo_db': 'placar_fora_2t', 'local': 'fora'},
        {'titulo': 'Mais Gols (Total Fora)', 'campo_db': 'placar_fora_total', 'local': 'fora'},
        
        # --- DEFESA (GOLS SOFRIDOS) ---
        {'titulo': 'Defesa Mais Vazada (Total em Casa)', 'campo_db': 'placar_fora_total', 'local': 'casa'},
        {'titulo': 'Defesa Mais Vazada (Total Fora)', 'campo_db': 'placar_casa_total', 'local': 'fora'},
        {'titulo': 'Defesa Menos Vazada (Total em Casa)', 'campo_db': 'placar_fora_total', 'local': 'casa', 'order': 'asc'},
        {'titulo': 'Defesa Menos Vazada (Total Fora)', 'campo_db': 'placar_casa_total', 'local': 'fora', 'order': 'asc'},

        # --- FINALIZAÇÕES ---
        {'titulo': 'Mais Finalizações (1ºT em Casa)', 'campo_db': 'finalizacao_casa_1t', 'local': 'casa'},
        {'titulo': 'Mais Finalizações (Total em Casa)', 'campo_db': 'finalizacao_casa_total', 'local': 'casa'},
        {'titulo': 'Mais Finalizações (1ºT Fora)', 'campo_db': 'finalizacao_fora_1t', 'local': 'fora'},
        {'titulo': 'Mais Finalizações (Total Fora)', 'campo_db': 'finalizacao_fora_total', 'local': 'fora'},
        {'titulo': 'Menos Finalizações (Total em Casa)', 'campo_db': 'finalizacao_casa_total', 'local': 'casa', 'order': 'asc'},
        {'titulo': 'Menos Finalizações (Total Fora)', 'campo_db': 'finalizacao_fora_total', 'local': 'fora', 'order': 'asc'},

        # --- CHUTES NO GOL ---
        {'titulo': 'Mais Chutes no Gol (1ºT em Casa)', 'campo_db': 'chutes_no_gol_casa_1t', 'local': 'casa'},
        {'titulo': 'Mais Chutes no Gol (Total em Casa)', 'campo_db': 'chutes_no_gol_casa_total', 'local': 'casa'},
        {'titulo': 'Mais Chutes no Gol (1ºT Fora)', 'campo_db': 'chutes_no_gol_fora_1t', 'local': 'fora'},
        {'titulo': 'Mais Chutes no Gol (Total Fora)', 'campo_db': 'chutes_no_gol_fora_total', 'local': 'fora'},
        {'titulo': 'Menos Chutes no Gol (Total em Casa)', 'campo_db': 'chutes_no_gol_casa_total', 'local': 'casa', 'order': 'asc'},
        {'titulo': 'Menos Chutes no Gol (Total Fora)', 'campo_db': 'chutes_no_gol_fora_total', 'local': 'fora', 'order': 'asc'},

        # --- ESCANTEIOS ---
        {'titulo': 'Mais Escanteios (1ºT em Casa)', 'campo_db': 'escanteios_casa_1t', 'local': 'casa'},
        {'titulo': 'Mais Escanteios (2ºT em Casa)', 'campo_db': 'escanteios_casa_2t', 'local': 'casa'},
        {'titulo': 'Mais Escanteios (Total em Casa)', 'campo_db': 'escanteios_casa_total', 'local': 'casa'},
        {'titulo': 'Mais Escanteios (1ºT Fora)', 'campo_db': 'escanteios_fora_1t', 'local': 'fora'},
        {'titulo': 'Mais Escanteios (2ºT Fora)', 'campo_db': 'escanteios_fora_2t', 'local': 'fora'},
        {'titulo': 'Mais Escanteios (Total Fora)', 'campo_db': 'escanteios_fora_total', 'local': 'fora'},
        {'titulo': 'Menos Escanteios (Total em Casa)', 'campo_db': 'escanteios_casa_total', 'local': 'casa', 'order': 'asc'},
        {'titulo': 'Menos Escanteios (Total Fora)', 'campo_db': 'escanteios_fora_total', 'local': 'fora', 'order': 'asc'},
        
        # --- CARTÕES AMARELOS ---
        {'titulo': 'Mais Cartões (1ºT em Casa)', 'campo_db': 'cartoes_amarelos_casa_1t', 'local': 'casa'},
        {'titulo': 'Mais Cartões (Total em Casa)', 'campo_db': 'cartoes_amarelos_casa_total', 'local': 'casa'},
        {'titulo': 'Mais Cartões (1ºT Fora)', 'campo_db': 'cartoes_amarelos_fora_1t', 'local': 'fora'},
        {'titulo': 'Mais Cartões (Total Fora)', 'campo_db': 'cartoes_amarelos_fora_total', 'local': 'fora'},
        {'titulo': 'Menos Cartões (Total em Casa)', 'campo_db': 'cartoes_amarelos_casa_total', 'local': 'casa', 'order': 'asc'},
        {'titulo': 'Menos Cartões (Total Fora)', 'campo_db': 'cartoes_amarelos_fora_total', 'local': 'fora', 'order': 'asc'},
    ]

    destaques_encontrados = []

    for ranking in rankings_de_interesse:
        try:
            campo_time_id = 'time_casa_id' if ranking['local'] == 'casa' else 'time_fora_id'
            campo_time_nome = 'time_casa__nome' if ranking['local'] == 'casa' else 'time_fora__nome'

            order = ranking.get('order', 'desc')
            order_by_clause = 'media' if order == 'asc' else '-media'

            # Nova abordagem: consultamos o modelo Jogo diretamente
            lider_query = Jogo.objects.filter(
                liga_id=liga_id
            ).values(
                campo_time_id,
                campo_time_nome
            ).annotate(
                media=Avg(ranking['campo_db'])
            ).filter(media__isnull=False).order_by(order_by_clause)

            lider = lider_query.first()

            if lider:
                destaques_encontrados.append({
                    "titulo": ranking['titulo'],
                    "time_nome": lider[campo_time_nome],
                    "media_estatistica": round(lider['media'], 2),
                    "ordem": order
                })
        except Exception as e:
            print(f"Erro ao calcular ranking '{ranking['titulo']}': {e}")
            continue
    destaques_encontrados.sort(key=lambda x: x['ordem'] == 'asc')
    return JsonResponse(destaques_encontrados, safe=False)
    

def rankings_page(request):
    """
    Renderiza o template HTML da página de Rankings.
    """
    # Esta view não precisa de nenhuma lógica complexa,
    # apenas de carregar o template. O JavaScript dentro do
    # template cuidará de buscar os dados da API.
    return render(request, 'app_analise/rankings.html')

def adicionar_liga(request):
    # Se o formulário foi enviado (método POST)
    if request.method == 'POST':
        # Pega o nome da liga que foi digitado no formulário
        nome_da_liga = request.POST.get('nome_liga')

        # Verifica se o nome não está vazio
        if nome_da_liga:
            # Cria um novo objeto Liga e salva no banco de dados
            nova_liga = Liga(nome=nome_da_liga)
            nova_liga.save()
            
            # Adiciona uma mensagem de sucesso
            messages.success(request, f'A liga "{nome_da_liga}" foi cadastrada com sucesso!')
            
            # Redireciona de volta para a mesma página (para limpar o formulário)
            return redirect('app_analise:adicionar_liga')
        else:
            # Adiciona uma mensagem de erro se o campo estiver vazio
            messages.error(request, 'O nome da liga não pode estar vazio.')

    # Se a página foi apenas acessada (método GET), apenas mostra a página
    return render(request, 'app_analise/adicionar_liga.html')

def gerenciar_ligas(request):
    # Busca todas as ligas cadastradas no banco de dados
    todas_as_ligas = Liga.objects.all()
    
    # Envia a lista de ligas para o template
    contexto = {
        'todas_as_ligas': todas_as_ligas
    }
    return render(request, 'app_analise/gerenciar_ligas.html', contexto)

def adicionar_time(request, liga_id):
    # Pega a liga específica do banco de dados ou retorna um erro 404 se não encontrar
    liga = get_object_or_404(Liga, id=liga_id)

    # Se o formulário de adicionar time foi enviado
    if request.method == 'POST':
        nome_do_time = request.POST.get('nome_time')
        if nome_do_time:
            # Verifica se o time já existe nessa liga
            if not Time.objects.filter(nome=nome_do_time, liga=liga).exists():
                # Cria o novo time, JÁ ASSOCIANDO COM A LIGA CORRETA
                novo_time = Time(nome=nome_do_time, liga=liga)
                novo_time.save()
                messages.success(request, f'Time "{nome_do_time}" adicionado com sucesso!')
            else:
                messages.error(request, f'O time "{nome_do_time}" já existe nesta liga.')
        
        # Redireciona para a mesma página para poder adicionar mais times
        return redirect('app_analise:adicionar_time', liga_id=liga.id)
    # Busca todos os times que já pertencem a esta liga para listá-los
    times_da_liga = Time.objects.filter(liga=liga)

    contexto = {
        'liga': liga,
        'times_da_liga': times_da_liga
    }
    return render(request, 'app_analise/adicionar_time.html', contexto)

def atualizar_estatisticas_do_jogo(jogo):
    """
    Esta função recebe um objeto 'jogo' recém-salvo e atualiza as
    estatísticas para o time da casa e o time de fora.
    """
    time_casa = jogo.time_casa
    time_fora = jogo.time_fora

    # --- SETUP: Pega ou cria o registro de estatísticas para cada time ---
    stats_casa, created_casa = AnaliseTime.objects.get_or_create(time=time_casa, defaults={'liga': time_casa.liga})
    stats_fora, created_fora = AnaliseTime.objects.get_or_create(time=time_fora, defaults={'liga': time_fora.liga})

    # =================================================================
    # --- ETAPA 1: ATUALIZAR ESTATÍSTICAS "EM CASA" PARA O TIME DA CASA ---
    # =================================================================
    jogos_casa_antigos = stats_casa.jogos_casa
    stats_casa.media_placar_casa_1t = ((stats_casa.media_placar_casa_1t * jogos_casa_antigos) + jogo.placar_casa_1t) / (jogos_casa_antigos + 1)
    stats_casa.media_placar_casa_2t = ((stats_casa.media_placar_casa_2t * jogos_casa_antigos) + jogo.placar_casa_2t) / (jogos_casa_antigos + 1)
    stats_casa.media_placar_casa_total = ((stats_casa.media_placar_casa_total * jogos_casa_antigos) + jogo.placar_casa_total) / (jogos_casa_antigos + 1)
    
    stats_casa.media_finalizacao_casa_1t = ((stats_casa.media_finalizacao_casa_1t * jogos_casa_antigos) + jogo.finalizacao_casa_1t) / (jogos_casa_antigos + 1)
    stats_casa.media_finalizacao_casa_2t = ((stats_casa.media_finalizacao_casa_2t * jogos_casa_antigos) + jogo.finalizacao_casa_2t) / (jogos_casa_antigos + 1)
    stats_casa.media_finalizacao_casa_total = ((stats_casa.media_finalizacao_casa_total * jogos_casa_antigos) + jogo.finalizacao_casa_total) / (jogos_casa_antigos + 1)

    stats_casa.media_chutes_no_gol_casa_1t = ((stats_casa.media_chutes_no_gol_casa_1t * jogos_casa_antigos) + jogo.chutes_no_gol_casa_1t) / (jogos_casa_antigos + 1)
    stats_casa.media_chutes_no_gol_casa_2t = ((stats_casa.media_chutes_no_gol_casa_2t * jogos_casa_antigos) + jogo.chutes_no_gol_casa_2t) / (jogos_casa_antigos + 1)
    stats_casa.media_chutes_no_gol_casa_total = ((stats_casa.media_chutes_no_gol_casa_total * jogos_casa_antigos) + jogo.chutes_no_gol_casa_total) / (jogos_casa_antigos + 1)

    stats_casa.media_escanteios_casa_1t = ((stats_casa.media_escanteios_casa_1t * jogos_casa_antigos) + jogo.escanteios_casa_1t) / (jogos_casa_antigos + 1)
    stats_casa.media_escanteios_casa_2t = ((stats_casa.media_escanteios_casa_2t * jogos_casa_antigos) + jogo.escanteios_casa_2t) / (jogos_casa_antigos + 1)
    stats_casa.media_escanteios_casa_total = ((stats_casa.media_escanteios_casa_total * jogos_casa_antigos) + jogo.escanteios_casa_total) / (jogos_casa_antigos + 1)

    stats_casa.media_cartoes_amarelos_casa_1t = ((stats_casa.media_cartoes_amarelos_casa_1t * jogos_casa_antigos) + jogo.cartoes_amarelos_casa_1t) / (jogos_casa_antigos + 1)
    stats_casa.media_cartoes_amarelos_casa_2t = ((stats_casa.media_cartoes_amarelos_casa_2t * jogos_casa_antigos) + jogo.cartoes_amarelos_casa_2t) / (jogos_casa_antigos + 1)
    stats_casa.media_cartoes_amarelos_casa_total = ((stats_casa.media_cartoes_amarelos_casa_total * jogos_casa_antigos) + jogo.cartoes_amarelos_casa_total) / (jogos_casa_antigos + 1)

    stats_casa.jogos_casa += 1

    # ===================================================================
    # --- ETAPA 2: ATUALIZAR ESTATÍSTICAS "FORA" PARA O TIME DE FORA ---
    # ===================================================================
    jogos_fora_antigos = stats_fora.jogos_fora
    stats_fora.media_placar_fora_1t = ((stats_fora.media_placar_fora_1t * jogos_fora_antigos) + jogo.placar_fora_1t) / (jogos_fora_antigos + 1)
    stats_fora.media_placar_fora_2t = ((stats_fora.media_placar_fora_2t * jogos_fora_antigos) + jogo.placar_fora_2t) / (jogos_fora_antigos + 1)
    stats_fora.media_placar_fora_total = ((stats_fora.media_placar_fora_total * jogos_fora_antigos) + jogo.placar_fora_total) / (jogos_fora_antigos + 1)

    stats_fora.media_finalizacao_fora_1t = ((stats_fora.media_finalizacao_fora_1t * jogos_fora_antigos) + jogo.finalizacao_fora_1t) / (jogos_fora_antigos + 1)
    stats_fora.media_finalizacao_fora_2t = ((stats_fora.media_finalizacao_fora_2t * jogos_fora_antigos) + jogo.finalizacao_fora_2t) / (jogos_fora_antigos + 1)
    stats_fora.media_finalizacao_fora_total = ((stats_fora.media_finalizacao_fora_total * jogos_fora_antigos) + jogo.finalizacao_fora_total) / (jogos_fora_antigos + 1)

    stats_fora.media_chutes_no_gol_fora_1t = ((stats_fora.media_chutes_no_gol_fora_1t * jogos_fora_antigos) + jogo.chutes_no_gol_fora_1t) / (jogos_fora_antigos + 1)
    stats_fora.media_chutes_no_gol_fora_2t = ((stats_fora.media_chutes_no_gol_fora_2t * jogos_fora_antigos) + jogo.chutes_no_gol_fora_2t) / (jogos_fora_antigos + 1)
    stats_fora.media_chutes_no_gol_fora_total = ((stats_fora.media_chutes_no_gol_fora_total * jogos_fora_antigos) + jogo.chutes_no_gol_fora_total) / (jogos_fora_antigos + 1)

    stats_fora.media_escanteios_fora_1t = ((stats_fora.media_escanteios_fora_1t * jogos_fora_antigos) + jogo.escanteios_fora_1t) / (jogos_fora_antigos + 1)
    stats_fora.media_escanteios_fora_2t = ((stats_fora.media_escanteios_fora_2t * jogos_fora_antigos) + jogo.escanteios_fora_2t) / (jogos_fora_antigos + 1)
    stats_fora.media_escanteios_fora_total = ((stats_fora.media_escanteios_fora_total * jogos_fora_antigos) + jogo.escanteios_fora_total) / (jogos_fora_antigos + 1)

    stats_fora.media_cartoes_amarelos_fora_1t = ((stats_fora.media_cartoes_amarelos_fora_1t * jogos_fora_antigos) + jogo.cartoes_amarelos_fora_1t) / (jogos_fora_antigos + 1)
    stats_fora.media_cartoes_amarelos_fora_2t = ((stats_fora.media_cartoes_amarelos_fora_2t * jogos_fora_antigos) + jogo.cartoes_amarelos_fora_2t) / (jogos_fora_antigos + 1)
    stats_fora.media_cartoes_amarelos_fora_total = ((stats_fora.media_cartoes_amarelos_fora_total * jogos_fora_antigos) + jogo.cartoes_amarelos_fora_total) / (jogos_fora_antigos + 1)

    stats_fora.jogos_fora += 1
    
    jogos_gerais_antigos_casa = stats_casa.jogos
    jogos_gerais_antigos_fora = stats_fora.jogos
    
    stats_casa.jogos += 1
    stats_fora.jogos += 1

    # --- ATUALIZAÇÃO GERAL PARA TIME DA CASA (usando dados de casa do jogo) ---
    stats_casa.media_placar_geral_1t = ((stats_casa.media_placar_geral_1t * jogos_gerais_antigos_casa) + jogo.placar_casa_1t) / stats_casa.jogos
    stats_casa.media_placar_geral_2t = ((stats_casa.media_placar_geral_2t * jogos_gerais_antigos_casa) + jogo.placar_casa_2t) / stats_casa.jogos
    stats_casa.media_placar_geral_total = ((stats_casa.media_placar_geral_total * jogos_gerais_antigos_casa) + jogo.placar_casa_total) / stats_casa.jogos
    
    stats_casa.media_finalizacao_geral_1t = ((stats_casa.media_finalizacao_geral_1t * jogos_gerais_antigos_casa) + jogo.finalizacao_casa_1t) / stats_casa.jogos
    stats_casa.media_finalizacao_geral_2t = ((stats_casa.media_finalizacao_geral_2t * jogos_gerais_antigos_casa) + jogo.finalizacao_casa_2t) / stats_casa.jogos
    stats_casa.media_finalizacao_geral_total = ((stats_casa.media_finalizacao_geral_total * jogos_gerais_antigos_casa) + jogo.finalizacao_casa_total) / stats_casa.jogos

    stats_casa.media_chutes_no_gol_geral_1t = ((stats_casa.media_chutes_no_gol_geral_1t * jogos_gerais_antigos_casa) + jogo.chutes_no_gol_casa_1t) / stats_casa.jogos
    stats_casa.media_chutes_no_gol_geral_2t = ((stats_casa.media_chutes_no_gol_geral_2t * jogos_gerais_antigos_casa) + jogo.chutes_no_gol_casa_2t) / stats_casa.jogos
    stats_casa.media_chutes_no_gol_geral_total = ((stats_casa.media_chutes_no_gol_geral_total * jogos_gerais_antigos_casa) + jogo.chutes_no_gol_casa_total) / stats_casa.jogos

    stats_casa.media_escanteios_geral_1t = ((stats_casa.media_escanteios_geral_1t * jogos_gerais_antigos_casa) + jogo.escanteios_casa_1t) / stats_casa.jogos
    stats_casa.media_escanteios_geral_2t = ((stats_casa.media_escanteios_geral_2t * jogos_gerais_antigos_casa) + jogo.escanteios_casa_2t) / stats_casa.jogos
    stats_casa.media_escanteios_geral_total = ((stats_casa.media_escanteios_geral_total * jogos_gerais_antigos_casa) + jogo.escanteios_casa_total) / stats_casa.jogos

    stats_casa.media_cartoes_amarelos_geral_1t = ((stats_casa.media_cartoes_amarelos_geral_1t * jogos_gerais_antigos_casa) + jogo.cartoes_amarelos_casa_1t) / stats_casa.jogos
    stats_casa.media_cartoes_amarelos_geral_2t = ((stats_casa.media_cartoes_amarelos_geral_2t * jogos_gerais_antigos_casa) + jogo.cartoes_amarelos_casa_2t) / stats_casa.jogos
    stats_casa.media_cartoes_amarelos_geral_total = ((stats_casa.media_cartoes_amarelos_geral_total * jogos_gerais_antigos_casa) + jogo.cartoes_amarelos_casa_total) / stats_casa.jogos

    # --- ATUALIZAÇÃO GERAL PARA TIME DE FORA (usando dados de fora do jogo) ---
    stats_fora.media_placar_geral_1t = ((stats_fora.media_placar_geral_1t * jogos_gerais_antigos_fora) + jogo.placar_fora_1t) / stats_fora.jogos
    stats_fora.media_placar_geral_2t = ((stats_fora.media_placar_geral_2t * jogos_gerais_antigos_fora) + jogo.placar_fora_2t) / stats_fora.jogos
    stats_fora.media_placar_geral_total = ((stats_fora.media_placar_geral_total * jogos_gerais_antigos_fora) + jogo.placar_fora_total) / stats_fora.jogos

    stats_fora.media_finalizacao_geral_1t = ((stats_fora.media_finalizacao_geral_1t * jogos_gerais_antigos_fora) + jogo.finalizacao_fora_1t) / stats_fora.jogos
    stats_fora.media_finalizacao_geral_2t = ((stats_fora.media_finalizacao_geral_2t * jogos_gerais_antigos_fora) + jogo.finalizacao_fora_2t) / stats_fora.jogos
    stats_fora.media_finalizacao_geral_total = ((stats_fora.media_finalizacao_geral_total * jogos_gerais_antigos_fora) + jogo.finalizacao_fora_total) / stats_fora.jogos

    stats_fora.media_chutes_no_gol_geral_1t = ((stats_fora.media_chutes_no_gol_geral_1t * jogos_gerais_antigos_fora) + jogo.chutes_no_gol_fora_1t) / stats_fora.jogos
    stats_fora.media_chutes_no_gol_geral_2t = ((stats_fora.media_chutes_no_gol_geral_2t * jogos_gerais_antigos_fora) + jogo.chutes_no_gol_fora_2t) / stats_fora.jogos
    stats_fora.media_chutes_no_gol_geral_total = ((stats_fora.media_chutes_no_gol_geral_total * jogos_gerais_antigos_fora) + jogo.chutes_no_gol_fora_total) / stats_fora.jogos

    stats_fora.media_escanteios_geral_1t = ((stats_fora.media_escanteios_geral_1t * jogos_gerais_antigos_fora) + jogo.escanteios_fora_1t) / stats_fora.jogos
    stats_fora.media_escanteios_geral_2t = ((stats_fora.media_escanteios_geral_2t * jogos_gerais_antigos_fora) + jogo.escanteios_fora_2t) / stats_fora.jogos
    stats_fora.media_escanteios_geral_total = ((stats_fora.media_escanteios_geral_total * jogos_gerais_antigos_fora) + jogo.escanteios_fora_total) / stats_fora.jogos

    stats_fora.media_cartoes_amarelos_geral_1t = ((stats_fora.media_cartoes_amarelos_geral_1t * jogos_gerais_antigos_fora) + jogo.cartoes_amarelos_fora_1t) / stats_fora.jogos
    stats_fora.media_cartoes_amarelos_geral_2t = ((stats_fora.media_cartoes_amarelos_geral_2t * jogos_gerais_antigos_fora) + jogo.cartoes_amarelos_fora_2t) / stats_fora.jogos
    stats_fora.media_cartoes_amarelos_geral_total = ((stats_fora.media_cartoes_amarelos_geral_total * jogos_gerais_antigos_fora) + jogo.cartoes_amarelos_fora_total) / stats_fora.jogos
    
    # --- SALVAR TUDO ---
    stats_casa.save()
    stats_fora.save()

    print(f"Estatísticas atualizadas para {time_casa.nome} e {time_fora.nome}")

def adicionar_jogo(request):
    # Lógica para quando o formulário é enviado
    if request.method == 'POST':
        # --- 1. Captura de todos os dados do formulário ---
        liga_id = request.POST.get('liga')
        time_casa_id = request.POST.get('time_casa')
        time_fora_id = request.POST.get('time_fora')
        
        # Pega os objetos do banco de dados
        liga = get_object_or_404(Liga, id=liga_id)
        time_casa = get_object_or_404(Time, id=time_casa_id)
        time_fora = get_object_or_404(Time, id=time_fora_id)

        # Cria uma instância do Jogo com os dados do formulário
        # Bloco para substituir a criação do novo_jogo em views.py

        novo_jogo = Jogo(
    liga=liga,
    rodada=int(request.POST.get('rodada') or 0),
    data=request.POST.get('data'),
    time_casa=time_casa,
    time_fora=time_fora,

    # --- Estatísticas do 1º Tempo ---
    placar_casa_1t=int(request.POST.get('placar_casa_1t') or 0),
    placar_fora_1t=int(request.POST.get('placar_fora_1t') or 0),
    finalizacao_casa_1t=int(request.POST.get('finalizacao_casa_1t') or 0),
    finalizacao_fora_1t=int(request.POST.get('finalizacao_fora_1t') or 0),
    chutes_no_gol_casa_1t=int(request.POST.get('chutes_no_gol_casa_1t') or 0),
    chutes_no_gol_fora_1t=int(request.POST.get('chutes_no_gol_fora_1t') or 0),
    escanteios_casa_1t=int(request.POST.get('escanteios_casa_1t') or 0),
    escanteios_fora_1t=int(request.POST.get('escanteios_fora_1t') or 0),
    cartoes_amarelos_casa_1t=int(request.POST.get('cartoes_amarelos_casa_1t') or 0),
    cartoes_amarelos_fora_1t=int(request.POST.get('cartoes_amarelos_fora_1t') or 0),

    # --- Estatísticas do 2º Tempo ---
    placar_casa_2t=int(request.POST.get('placar_casa_2t') or 0),
    placar_fora_2t=int(request.POST.get('placar_fora_2t') or 0),
    finalizacao_casa_2t=int(request.POST.get('finalizacao_casa_2t') or 0),
    finalizacao_fora_2t=int(request.POST.get('finalizacao_fora_2t') or 0),
    chutes_no_gol_casa_2t=int(request.POST.get('chutes_no_gol_casa_2t') or 0),
    chutes_no_gol_fora_2t=int(request.POST.get('chutes_no_gol_fora_2t') or 0),
    escanteios_casa_2t=int(request.POST.get('escanteios_casa_2t') or 0),
    escanteios_fora_2t=int(request.POST.get('escanteios_fora_2t') or 0),
    cartoes_amarelos_casa_2t=int(request.POST.get('cartoes_amarelos_casa_2t') or 0),
    cartoes_amarelos_fora_2t=int(request.POST.get('cartoes_amarelos_fora_2t') or 0),
)

        # --- 2. Lógica para calcular os totais (como no Excel) ---
        novo_jogo.placar_casa_total = int(novo_jogo.placar_casa_1t) + int(novo_jogo.placar_casa_2t)
        novo_jogo.placar_fora_total = int(novo_jogo.placar_fora_1t) + int(novo_jogo.placar_fora_2t)
        # ... continue essa lógica para os outros totais (finalização, chutes, etc) ...
        # Bloco para calcular os totais em views.py

        # Dica: Usamos 'or 0' para o caso de um campo vir vazio, evitando erros.
        novo_jogo.placar_casa_total = int(novo_jogo.placar_casa_1t or 0) + int(novo_jogo.placar_casa_2t or 0)
        novo_jogo.placar_fora_total = int(novo_jogo.placar_fora_1t or 0) + int(novo_jogo.placar_fora_2t or 0)

        novo_jogo.finalizacao_casa_total = int(novo_jogo.finalizacao_casa_1t or 0) + int(novo_jogo.finalizacao_casa_2t or 0)
        novo_jogo.finalizacao_fora_total = int(novo_jogo.finalizacao_fora_1t or 0) + int(novo_jogo.finalizacao_fora_2t or 0)

        novo_jogo.chutes_no_gol_casa_total = int(novo_jogo.chutes_no_gol_casa_1t or 0) + int(novo_jogo.chutes_no_gol_casa_2t or 0)
        novo_jogo.chutes_no_gol_fora_total = int(novo_jogo.chutes_no_gol_fora_1t or 0) + int(novo_jogo.chutes_no_gol_fora_2t or 0)

        novo_jogo.escanteios_casa_total = int(novo_jogo.escanteios_casa_1t or 0) + int(novo_jogo.escanteios_casa_2t or 0)
        novo_jogo.escanteios_fora_total = int(novo_jogo.escanteios_fora_1t or 0) + int(novo_jogo.escanteios_fora_2t or 0)

        novo_jogo.cartoes_amarelos_casa_total = int(novo_jogo.cartoes_amarelos_casa_1t or 0) + int(novo_jogo.cartoes_amarelos_casa_2t or 0)
        novo_jogo.cartoes_amarelos_fora_total = int(novo_jogo.cartoes_amarelos_fora_1t or 0) + int(novo_jogo.cartoes_amarelos_fora_2t or 0)
        # --- 3. Salva o novo jogo no banco de dados ---
        novo_jogo.save()

        # --- 4. DISPARA A ATUALIZAÇÃO DAS ESTATÍSTICAS ---
        # (Ainda vamos criar esta função, mas já vamos chamá-la aqui)
        atualizar_estatisticas_do_jogo(novo_jogo)

        messages.success(request, f'Jogo {time_casa.nome} vs {time_fora.nome} salvo com sucesso!')
        return redirect('app_analise:adicionar_jogo')

    # Lógica para quando a página é acessada (GET)
    else:
        todas_as_ligas = Liga.objects.all()
        contexto = {
            'todas_as_ligas': todas_as_ligas
        }
        return render(request, 'app_analise/adicionar_jogo.html', contexto)
    
def get_times_for_liga(request, liga_id):
    # Filtra os times que pertencem à liga com o ID fornecido
    times = Time.objects.filter(liga_id=liga_id).order_by('nome')
    # Converte a lista de times para um formato que o JavaScript entende (JSON)
    lista_de_times = list(times.values('id', 'nome'))
    return JsonResponse({'times': lista_de_times})

def ver_jogos_liga(request, liga_id):
    # Pega a liga específica ou retorna erro 404
    liga = get_object_or_404(Liga, id=liga_id)
    
    # Busca todos os jogos pertencentes a esta liga, ordenados pela data mais recente
    jogos_da_liga = Jogo.objects.filter(liga=liga).order_by('-data', '-rodada')
    
    contexto = {
        'liga': liga,
        'jogos_da_liga': jogos_da_liga
    }
    return render(request, 'app_analise/ver_jogos_liga.html', contexto)

@login_required

def home(request, banca_id=None, year=None, month=None): # <<< MUDANÇA 1: Adicionado 'banca_id=None'
    # --- 1. DEFINE A DATA DE REFERÊNCIA ---
    today = date.today()
    if year is None or month is None:
        year, month = today.year, today.month
    current_date = date(year, month, 1)

    # --- 2. CALCULA MÊS ANTERIOR E PRÓXIMO ---
    prev_month_date = current_date - timedelta(days=1)
    next_month_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1) # Lógica mais robusta
    is_future = next_month_date > today.replace(day=1)

    # --- 3. LÓGICA DE SELEÇÃO DA BANCA (MUDANÇA PRINCIPAL) ---
    banca_selecionada = None # <<< MUDANÇA 2: Começa como Nulo
    if banca_id:
        # Se um ID de banca veio da URL, usa essa banca
        banca_selecionada = get_object_or_404(Banca, id=banca_id)
    else:
        # Se não, pega a primeira banca ativa como padrão
        banca_selecionada = Banca.objects.filter(ativa=True).first()

    # --- 4. PREPARAÇÃO DO CONTEXTO ---
    # Busca todas as bancas para popular o menu de seleção
    todas_as_bancas = Banca.objects.all().order_by('nome')
    
    contexto = {
        'year': year,
        'month_name': calendar.month_name[month].upper(),
        'banca_selecionada': banca_selecionada, # <<< MUDANÇA 3: Usa 'banca_selecionada'
        'todas_as_bancas': todas_as_bancas, # <<< MUDANÇA 4: Adiciona a lista de todas as bancas
        'kpis': None, 'top_mercados': None, 'month_days': [], 'daily_results': {},
        'prev_year': prev_month_date.year,
        'prev_month': prev_month_date.month,
        'next_year': next_month_date.year,
        'next_month': next_month_date.month,
        'is_future': is_future,
    }

    # --- 5. BUSCA DE DADOS (agora usa a 'banca_selecionada') ---
    if banca_selecionada: # <<< MUDANÇA 5: Troca 'banca_ativa' por 'banca_selecionada'
        # Busca apostas usando as variáveis 'year' e 'month'
        apostas_do_mes = Aposta.objects.filter(
            banca=banca_selecionada, data__year=year, data__month=month
        ).exclude(resultado='PENDING')
        
        # O resto do seu código para calcular 'daily_results', 'month_days', 'kpis', e 'top_mercados'
        # continua exatamente o mesmo, apenas usando a variável 'banca_selecionada'
        # no lugar de 'banca_ativa'.
        # (Vou colar o resto do seu código aqui para garantir)
        resultados_diarios_qs = apostas_do_mes.values('data__day').annotate(total_retorno=Sum('retorno'))
        daily_results = {}
        for resultado_dia in resultados_diarios_qs:
            dia = resultado_dia['data__day']
            total_retorno = resultado_dia['total_retorno']
            if total_retorno is not None and banca_selecionada.valor_inicial > 0:
                percentual = (total_retorno / banca_selecionada.valor_inicial) * 100
                daily_results[dia] = round(percentual, 2)
        
        contexto['daily_results'] = daily_results

        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(year, month)
        contexto['month_days'] = month_days

        if apostas_do_mes.exists():
            kpis = apostas_do_mes.aggregate(
                lucro_total=Coalesce(Sum('retorno'), Decimal('0.0')),
                total_apostado=Coalesce(Sum('valor_apostado'), Decimal('0.0')),
                odd_media=Coalesce(Avg('odd'), Decimal('0.0')),
                total_apostas=Count('id'),
                greens=Count('id', filter=Q(resultado='GREEN'))
            )
            if banca_selecionada.valor_inicial > 0:
                kpis['crescimento_banca'] = (kpis['lucro_total'] / banca_selecionada.valor_inicial) * 100
            else:
                kpis['crescimento_banca'] = 0
            kpis['roi'] = (kpis['lucro_total'] / kpis['total_apostado']) * 100 if kpis['total_apostado'] > 0 else 0
            kpis['taxa_acerto'] = (kpis['greens'] / kpis['total_apostas']) * 100 if kpis['total_apostas'] > 0 else 0
            contexto['kpis'] = kpis
        
        top_mercados = Aposta.objects.filter(banca=banca_selecionada, resultado='GREEN').values('mercado').annotate(
            lucro=Sum('retorno')
        ).order_by('-lucro').filter(lucro__gt=0)[:3]
        contexto['top_mercados'] = top_mercados
    
    # --- DADOS FINAIS (para a Análise Comparativa) ---
    todas_as_ligas = Liga.objects.all()
    contexto['todas_as_ligas'] = todas_as_ligas
    
    return render(request, 'app_analise/home.html', contexto)


def comparar_times_api(request):
    time_a_id = request.GET.get('time_a')
    time_b_id = request.GET.get('time_b')

    # Busca as estatísticas dos dois times
    stats_a = get_object_or_404(AnaliseTime, time_id=time_a_id)
    stats_b = get_object_or_404(AnaliseTime, time_id=time_b_id)

    # Prepara os dados para o gráfico
    data = {
        'labels': ['Média Gols Marcados', 'Média Gols Sofridos', 'Média Finalizações', 'Média Escanteios'],
        'time_a': {
            'nome': stats_a.time.nome,
            'stats': [
                stats_a.media_placar_geral_total,
                stats_b.media_placar_geral_total, # Média de gols sofridos pelo time A é a média de gols marcados pelo adversário (simplificação)
                stats_a.media_finalizacao_geral_total,
                stats_a.media_escanteios_geral_total,
            ]
        },
        'time_b': {
            'nome': stats_b.time.nome,
            'stats': [
                stats_b.media_placar_geral_total,
                stats_a.media_placar_geral_total, # Média de gols sofridos pelo time B é a média de gols marcados pelo adversário (simplificação)
                stats_b.media_finalizacao_geral_total,
                stats_b.media_escanteios_geral_total,
            ]
        }
    }
    return JsonResponse(data)


def get_team_stats(request, time_id):
    # Busca as estatísticas do time ou retorna erro 404
    stats = get_object_or_404(AnaliseTime, time_id=time_id)
    
    # Monta um dicionário com os dados que queremos mostrar no gráfico
    data = {
        'nome': stats.time.nome,
        'media_gols_total': stats.media_placar_geral_total,
        'media_finalizacoes_total': stats.media_finalizacao_geral_total,
        'media_chutes_no_gol_total': stats.media_chutes_no_gol_geral_total,
        'media_escanteios_total': stats.media_escanteios_geral_total,
    }
    return JsonResponse(data)


def teste_card_view(request, time_a_id, time_b_id):
    contexto = {}
    try:
        analise_a = AnaliseTime.objects.get(time_id=time_a_id)
        analise_b = AnaliseTime.objects.get(time_id=time_b_id)
        
        # Esta função interna é a mesma que já existe na sua view painel_de_analise
        def calcular_medias_sofridas(time_obj, local):
            medias = {}
            jogos = Jogo.objects.filter(time_casa=time_obj.time) if local == 'casa' else Jogo.objects.filter(time_fora=time_obj.time)
            jogos_count = time_obj.jogos_casa if local == 'casa' else time_obj.jogos_fora
            campos_map = { 'gols': {'casa': 'placar_fora', 'fora': 'placar_casa'}, 'finalizacoes': {'casa': 'finalizacao_fora', 'fora': 'finalizacao_casa'}, 'chutes': {'casa': 'chutes_no_gol_fora', 'fora': 'chutes_no_gol_casa'}, 'escanteios': {'casa': 'escanteios_fora', 'fora': 'escanteios_casa'}, 'cartoes': {'casa': 'cartoes_amarelos_fora', 'fora': 'cartoes_amarelos_casa'} }
            for stat_name, field_map in campos_map.items():
                base_field = field_map[local]
                total_1t = jogos.aggregate(soma=Sum(f'{base_field}_1t'))['soma'] or 0
                total_2t = jogos.aggregate(soma=Sum(f'{base_field}_2t'))['soma'] or 0
                medias[f'{stat_name}_1t'] = total_1t / jogos_count if jogos_count > 0 else 0
                medias[f'{stat_name}_2t'] = total_2t / jogos_count if jogos_count > 0 else 0
            return medias

        medias_sofridas_a = calcular_medias_sofridas(analise_a, 'casa')
        medias_sofridas_b = calcular_medias_sofridas(analise_b, 'fora')
        
        stats_data = {
            'time_a': {'gols_marcados_1t': analise_a.media_placar_casa_1t, 'gols_marcados_2t': analise_a.media_placar_casa_2t, 'gols_sofridos_1t': medias_sofridas_a.get('gols_1t', 0), 'gols_sofridos_2t': medias_sofridas_a.get('gols_2t', 0), 'finalizacoes_marcados_1t': analise_a.media_finalizacao_casa_1t, 'finalizacoes_marcados_2t': analise_a.media_finalizacao_casa_2t, 'finalizacoes_sofridos_1t': medias_sofridas_a.get('finalizacoes_1t', 0), 'finalizacoes_sofridos_2t': medias_sofridas_a.get('finalizacoes_2t', 0), 'chutes_marcados_1t': analise_a.media_chutes_no_gol_casa_1t, 'chutes_marcados_2t': analise_a.media_chutes_no_gol_casa_2t, 'chutes_sofridos_1t': medias_sofridas_a.get('chutes_1t', 0), 'chutes_sofridos_2t': medias_sofridas_a.get('chutes_2t', 0), 'escanteios_marcados_1t': analise_a.media_escanteios_casa_1t, 'escanteios_marcados_2t': analise_a.media_escanteios_casa_2t, 'escanteios_sofridos_1t': medias_sofridas_a.get('escanteios_1t', 0), 'escanteios_sofridos_2t': medias_sofridas_a.get('escanteios_2t', 0), 'cartoes_marcados_1t': analise_a.media_cartoes_amarelos_casa_1t, 'cartoes_marcados_2t': analise_a.media_cartoes_amarelos_casa_2t, 'cartoes_sofridos_1t': medias_sofridas_a.get('cartoes_1t', 0), 'cartoes_sofridos_2t': medias_sofridas_a.get('cartoes_2t', 0)},
            'time_b': {'gols_marcados_1t': analise_b.media_placar_fora_1t, 'gols_marcados_2t': analise_b.media_placar_fora_2t, 'gols_sofridos_1t': medias_sofridas_b.get('gols_1t', 0), 'gols_sofridos_2t': medias_sofridas_b.get('gols_2t', 0), 'finalizacoes_marcados_1t': analise_b.media_finalizacao_fora_1t, 'finalizacoes_marcados_2t': analise_b.media_finalizacao_fora_2t, 'finalizacoes_sofridos_1t': medias_sofridas_b.get('finalizacoes_1t', 0), 'finalizacoes_sofridos_2t': medias_sofridas_b.get('finalizacoes_2t', 0), 'chutes_marcados_1t': analise_b.media_chutes_no_gol_fora_1t, 'chutes_marcados_2t': analise_b.media_chutes_no_gol_fora_2t, 'chutes_sofridos_1t': medias_sofridas_b.get('chutes_1t', 0), 'chutes_sofridos_2t': medias_sofridas_b.get('chutes_2t', 0), 'escanteios_marcados_1t': analise_b.media_escanteios_fora_1t, 'escanteios_marcados_2t': analise_b.media_escanteios_fora_2t, 'escanteios_sofridos_1t': medias_sofridas_b.get('escanteios_1t', 0), 'escanteios_sofridos_2t': medias_sofridas_b.get('escanteios_2t', 0), 'cartoes_marcados_1t': analise_b.media_cartoes_amarelos_fora_1t, 'cartoes_marcados_2t': analise_b.media_cartoes_amarelos_fora_2t, 'cartoes_sofridos_1t': medias_sofridas_b.get('cartoes_1t', 0), 'cartoes_sofridos_2t': medias_sofridas_b.get('cartoes_2t', 0)}
        }
        contexto['stats_json'] = mark_safe(json.dumps(stats_data))
    except AnaliseTime.DoesNotExist:
        contexto['erro'] = "Dados não encontrados para um dos times."

    return render(request, 'app_analise/teste_card.html', contexto)

def get_custom_stats_api(request, time_a_id, time_b_id):
    try:
        analise_a = AnaliseTime.objects.get(time_id=time_a_id)
        analise_b = AnaliseTime.objects.get(time_id=time_b_id)
        
        # APENAS CHAMA A FUNÇÃO AUXILIAR
        medias_sofridas_a = calcular_medias_sofridas(analise_a, 'casa')
        medias_sofridas_b = calcular_medias_sofridas(analise_b, 'fora')

        # Monta o dicionário de dados (sem alterações)
        stats_data = {
            'time_a': {
                'gols_marcados_1t': analise_a.media_placar_casa_1t, 'gols_marcados_2t': analise_a.media_placar_casa_2t, 'gols_marcados_total': analise_a.media_placar_casa_total,
                'gols_sofridos_1t': medias_sofridas_a.get('gols_1t', 0), 'gols_sofridos_2t': medias_sofridas_a.get('gols_2t', 0), 'gols_sofridos_total': medias_sofridas_a.get('gols_total', 0),
                'finalizacoes_marcados_1t': analise_a.media_finalizacao_casa_1t, 'finalizacoes_marcados_2t': analise_a.media_finalizacao_casa_2t, 'finalizacoes_marcados_total': analise_a.media_finalizacao_casa_total,
                'finalizacoes_sofridos_1t': medias_sofridas_a.get('finalizacoes_1t', 0), 'finalizacoes_sofridos_2t': medias_sofridas_a.get('finalizacoes_2t', 0), 'finalizacoes_sofridos_total': medias_sofridas_a.get('finalizacoes_total', 0),
                'chutes_marcados_1t': analise_a.media_chutes_no_gol_casa_1t, 'chutes_marcados_2t': analise_a.media_chutes_no_gol_casa_2t, 'chutes_marcados_total': analise_a.media_chutes_no_gol_casa_total,
                'chutes_sofridos_1t': medias_sofridas_a.get('chutes_1t', 0), 'chutes_sofridos_2t': medias_sofridas_a.get('chutes_2t', 0), 'chutes_sofridos_total': medias_sofridas_a.get('chutes_total', 0),
                'escanteios_marcados_1t': analise_a.media_escanteios_casa_1t, 'escanteios_marcados_2t': analise_a.media_escanteios_casa_2t, 'escanteios_marcados_total': analise_a.media_escanteios_casa_total,
                'escanteios_sofridos_1t': medias_sofridas_a.get('escanteios_1t', 0), 'escanteios_sofridos_2t': medias_sofridas_a.get('escanteios_2t', 0), 'escanteios_sofridos_total': medias_sofridas_a.get('escanteios_total', 0),
                'cartoes_marcados_1t': analise_a.media_cartoes_amarelos_casa_1t, 'cartoes_marcados_2t': analise_a.media_cartoes_amarelos_casa_2t, 'cartoes_marcados_total': analise_a.media_cartoes_amarelos_casa_total,
            },
            'time_b': {
                'gols_marcados_1t': analise_b.media_placar_fora_1t, 'gols_marcados_2t': analise_b.media_placar_fora_2t, 'gols_marcados_total': analise_b.media_placar_fora_total,
                'gols_sofridos_1t': medias_sofridas_b.get('gols_1t', 0), 'gols_sofridos_2t': medias_sofridas_b.get('gols_2t', 0), 'gols_sofridos_total': medias_sofridas_b.get('gols_total', 0),
                'finalizacoes_marcados_1t': analise_b.media_finalizacao_fora_1t, 'finalizacoes_marcados_2t': analise_b.media_finalizacao_fora_2t, 'finalizacoes_marcados_total': analise_b.media_finalizacao_fora_total,
                'finalizacoes_sofridos_1t': medias_sofridas_b.get('finalizacoes_1t', 0), 'finalizacoes_sofridos_2t': medias_sofridas_b.get('finalizacoes_2t', 0), 'finalizacoes_sofridos_total': medias_sofridas_b.get('finalizacoes_total', 0),
                'chutes_marcados_1t': analise_b.media_chutes_no_gol_fora_1t, 'chutes_marcados_2t': analise_b.media_chutes_no_gol_fora_2t, 'chutes_marcados_total': analise_b.media_chutes_no_gol_fora_total,
                'chutes_sofridos_1t': medias_sofridas_b.get('chutes_1t', 0), 'chutes_sofridos_2t': medias_sofridas_b.get('chutes_2t', 0), 'chutes_sofridos_total': medias_sofridas_b.get('chutes_total', 0),
                'escanteios_marcados_1t': analise_b.media_escanteios_fora_1t, 'escanteios_marcados_2t': analise_b.media_escanteios_fora_2t, 'escanteios_marcados_total': analise_b.media_escanteios_fora_total,
                'escanteios_sofridos_1t': medias_sofridas_b.get('escanteios_1t', 0), 'escanteios_sofridos_2t': medias_sofridas_b.get('escanteios_2t', 0), 'escanteios_sofridos_total': medias_sofridas_b.get('escanteios_total', 0),
                'cartoes_marcados_1t': analise_b.media_cartoes_amarelos_fora_1t, 'cartoes_marcados_2t': analise_b.media_cartoes_amarelos_fora_2t, 'cartoes_marcados_total': analise_b.media_cartoes_amarelos_fora_total,
        }
        }
        return JsonResponse(stats_data)
        
    except AnaliseTime.DoesNotExist:
        return JsonResponse({'erro': 'Time não encontrado'}, status=404)

def calcular_medias_sofridas(time_obj, local):
    # ... (código completo da função, sem alterações) ...
    medias = {}; jogos = Jogo.objects.filter(time_casa=time_obj.time) if local == 'casa' else Jogo.objects.filter(time_fora=time_obj.time); jogos_count = time_obj.jogos_casa if local == 'casa' else time_obj.jogos_fora; campos_map = { 'gols': {'casa': 'placar_fora', 'fora': 'placar_casa'}, 'finalizacoes': {'casa': 'finalizacao_fora', 'fora': 'finalizacao_casa'}, 'chutes': {'casa': 'chutes_no_gol_fora', 'fora': 'chutes_no_gol_casa'}, 'escanteios': {'casa': 'escanteios_fora', 'fora': 'escanteios_casa'}, 'cartoes': {'casa': 'cartoes_amarelos_fora', 'fora': 'cartoes_amarelos_casa'} };
    for stat_name, field_map in campos_map.items():
        base_field = field_map[local]; total_1t = jogos.aggregate(soma=Sum(f'{base_field}_1t'))['soma'] or 0; total_2t = jogos.aggregate(soma=Sum(f'{base_field}_2t'))['soma'] or 0; medias[f'{stat_name}_1t'] = total_1t / jogos_count if jogos_count > 0 else 0; medias[f'{stat_name}_2t'] = total_2t / jogos_count if jogos_count > 0 else 0; medias[f'{stat_name}_total'] = medias[f'{stat_name}_1t'] + medias[f'{stat_name}_2t']
    return medias

