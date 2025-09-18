# Path: app_analise/management/commands/importar_dados.py (VERSÃO CORRIGIDA)

import pandas as pd
from django.core.management.base import BaseCommand
from app_analise.models import Liga, Time, Jogo, AnaliseTime

class Command(BaseCommand):
    help = 'Lê o arquivo Excel, popula jogos e análises completas.'

    def handle(self, *args, **options):
        caminho_arquivo = 'dados_futebol_placardefutebol.xlsx'
        
        try:
            df_jogos = pd.read_excel(caminho_arquivo, sheet_name='Estatisticas Jogos')
            df_analise = pd.read_excel(caminho_arquivo, sheet_name='Analise Estatistica')
            self.stdout.write(self.style.SUCCESS(f"Arquivo '{caminho_arquivo}' lido com sucesso."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao ler o arquivo Excel: {e}"))
            return

        self.stdout.write("Limpando dados antigos do banco de dados...")
        Jogo.objects.all().delete()
        AnaliseTime.objects.all().delete()
        Time.objects.all().delete()
        Liga.objects.all().delete()

        # Criar Ligas e Times
        ligas = {nome: Liga.objects.create(nome=nome) for nome in df_jogos['Liga'].unique()}
        times = {}
        # Garante que todos os times de ambas as planilhas sejam criados
        todos_os_times = set(df_jogos['Time_Casa']).union(set(df_jogos['Time_Fora'])).union(set(df_analise['Time']))
        
        # Mapeia time para sua liga (assumindo que um time pertence a uma única liga principal no arquivo)
        mapa_time_liga = {}
        for _, row in df_jogos.iterrows():
            mapa_time_liga[row['Time_Casa']] = row['Liga']
            mapa_time_liga[row['Time_Fora']] = row['Liga']
            
        for nome_time in todos_os_times:
            if nome_time not in times and nome_time in mapa_time_liga:
                liga_nome = mapa_time_liga[nome_time]
                times[nome_time] = Time.objects.create(nome=nome_time, liga=ligas[liga_nome])
        
        self.stdout.write("Importando dados dos jogos...")
        jogos_para_criar = []
        for _, row in df_jogos.iterrows():
            jogo_data = {
                'id_jogo': row.get('id_jogo'), 'liga': ligas[row['Liga']], 'rodada': row.get('Rodada'), 'data': row.get('Data'),
                'time_casa': times[row['Time_Casa']], 'time_fora': times[row['Time_Fora']],
                'placar_casa_1t': row.get('Placar_Casa_1T', 0), 'placar_fora_1t': row.get('Placar_Fora_1T', 0),
                'placar_casa_2t': row.get('Placar_Casa_2T', 0), 'placar_fora_2t': row.get('Placar_Fora_2T', 0),
                'placar_casa_total': row.get('Placar_Casa_Total', 0), 'placar_fora_total': row.get('Placar_Fora_Total', 0),
                'finalizacao_casa_1t': row.get('Finalizacao_Casa_1T', 0), 'finalizacao_fora_1t': row.get('Finalizacao_Fora_1T', 0),
                'finalizacao_casa_2t': row.get('Finalizacao_Casa_2T', 0), 'finalizacao_fora_2t': row.get('Finalizacao_Fora_2T', 0),
                'finalizacao_casa_total': row.get('Finalizacao_Casa_Total', 0), 'finalizacao_fora_total': row.get('Finalizacao_Fora_Total', 0),
                'chutes_no_gol_casa_1t': row.get('Chutes_no_Gol_Casa_1T', 0), 'chutes_no_gol_fora_1t': row.get('Chutes_no_Gol_Fora_1T', 0),
                'chutes_no_gol_casa_2t': row.get('Chutes_no_Gol_Casa_2T', 0), 'chutes_no_gol_fora_2t': row.get('Chutes_no_Gol_Fora_2T', 0),
                'chutes_no_gol_casa_total': row.get('Chutes_no_Gol_Casa_Total', 0), 'chutes_no_gol_fora_total': row.get('Chutes_no_Gol_Fora_Total', 0),
                'escanteios_casa_1t': row.get('Escanteios_Casa_1T', 0), 'escanteios_fora_1t': row.get('Escanteios_Fora_1T', 0),
                'escanteios_casa_2t': row.get('Escanteios_Casa_2T', 0), 'escanteios_fora_2t': row.get('Escanteios_Fora_2T', 0),
                'escanteios_casa_total': row.get('Escanteios_Casa_Total', 0), 'escanteios_fora_total': row.get('Escanteios_Fora_Total', 0),
                'cartoes_amarelos_casa_1t': row.get('Cartoes_Amarelos_Casa_1T', 0), 'cartoes_amarelos_fora_1t': row.get('Cartoes_Amarelos_Fora_1T', 0),
                'cartoes_amarelos_casa_2t': row.get('Cartoes_Amarelos_Casa_2T', 0), 'cartoes_amarelos_fora_2t': row.get('Cartoes_Amarelos_Fora_2T', 0),
                'cartoes_amarelos_casa_total': row.get('Cartoes_Amarelos_Casa_Total', 0), 'cartoes_amarelos_fora_total': row.get('Cartoes_Amarelos_Fora_Total', 0),
            }
            jogos_para_criar.append(Jogo(**jogo_data))
        Jogo.objects.bulk_create(jogos_para_criar)
        self.stdout.write(self.style.SUCCESS(f"{len(jogos_para_criar)} jogos importados."))

        self.stdout.write("Importando dados da análise...")
        analises_para_criar = []
        for _, row in df_analise.iterrows():
            analise_data = {
                'liga': ligas[row['Liga']], 'time': times[row['Time']], 'jogos_total': row.get('Jogos', 0), 'jogos_casa': row.get('Jogos_Casa', 0), 'jogos_fora': row.get('Jogos_Fora', 0),
                'media_placar_casa_1t': row.get('Media_Placar_Casa_1T', 0), 'media_placar_fora_1t': row.get('Media_Placar_Fora_1T', 0), 'media_placar_casa_2t': row.get('Media_Placar_Casa_2T', 0), 'media_placar_fora_2t': row.get('Media_Placar_Fora_2T', 0), 'media_placar_casa_total': row.get('Media_Placar_Casa_Total', 0), 'media_placar_fora_total': row.get('Media_Placar_Fora_Total', 0), 'media_placar_geral_1t': row.get('Media_Placar_Geral_1T', 0), 'media_placar_geral_2t': row.get('Media_Placar_Geral_2T', 0), 'media_placar_geral_total': row.get('Media_Placar_Geral_Total', 0),
                'media_finalizacao_casa_1t': row.get('Media_Finalizacao_Casa_1T', 0), 'media_finalizacao_fora_1t': row.get('Media_Finalizacao_Fora_1T', 0), 'media_finalizacao_casa_2t': row.get('Media_Finalizacao_Casa_2T', 0), 'media_finalizacao_fora_2t': row.get('Media_Finalizacao_Fora_2T', 0), 'media_finalizacao_casa_total': row.get('Media_Finalizacao_Casa_Total', 0), 'media_finalizacao_fora_total': row.get('Media_Finalizacao_Fora_Total', 0), 'media_finalizacao_geral_1t': row.get('Media_Finalizacao_Geral_1T', 0), 'media_finalizacao_geral_2t': row.get('Media_Finalizacao_Geral_2T', 0), 'media_finalizacao_geral_total': row.get('Media_Finalizacao_Geral_Total', 0),
                'media_chutes_no_gol_casa_1t': row.get('Media_Chutes_no_Gol_Casa_1T', 0), 'media_chutes_no_gol_fora_1t': row.get('Media_Chutes_no_Gol_Fora_1T', 0), 'media_chutes_no_gol_casa_2t': row.get('Media_Chutes_no_Gol_Casa_2T', 0), 'media_chutes_no_gol_fora_2t': row.get('Media_Chutes_no_Gol_Fora_2T', 0), 'media_chutes_no_gol_casa_total': row.get('Media_Chutes_no_Gol_Casa_Total', 0), 'media_chutes_no_gol_fora_total': row.get('Media_Chutes_no_Gol_Fora_Total', 0), 'media_chutes_no_gol_geral_1t': row.get('Media_Chutes_no_Gol_Geral_1T', 0), 'media_chutes_no_gol_geral_2t': row.get('Media_Chutes_no_Gol_Geral_2T', 0), 'media_chutes_no_gol_geral_total': row.get('Media_Chutes_no_Gol_Geral_Total', 0),
                'media_escanteios_casa_1t': row.get('Media_Escanteios_Casa_1T', 0), 'media_escanteios_fora_1t': row.get('Media_Escanteios_Fora_1T', 0), 'media_escanteios_casa_2t': row.get('Media_Escanteios_Casa_2T', 0), 'media_escanteios_fora_2t': row.get('Media_Escanteios_Fora_2T', 0), 'media_escanteios_casa_total': row.get('Media_Escanteios_Casa_Total', 0), 'media_escanteios_fora_total': row.get('Media_Escanteios_Fora_Total', 0), 'media_escanteios_geral_1t': row.get('Media_Escanteios_Geral_1T', 0), 'media_escanteios_geral_2t': row.get('Media_Escanteios_Geral_2T', 0), 'media_escanteios_geral_total': row.get('Media_Escanteios_Geral_Total', 0),
                'media_cartoes_amarelos_casa_1t': row.get('Media_Cartoes_Amarelos_Casa_1T', 0), 'media_cartoes_amarelos_fora_1t': row.get('Media_Cartoes_Amarelos_Fora_1T', 0), 'media_cartoes_amarelos_casa_2t': row.get('Media_Cartoes_Amarelos_Casa_2T', 0), 'media_cartoes_amarelos_fora_2t': row.get('Media_Cartoes_Amarelos_Fora_2T', 0), 'media_cartoes_amarelos_casa_total': row.get('Media_Cartoes_Amarelos_Casa_Total', 0), 'media_cartoes_amarelos_fora_total': row.get('Media_Cartoes_Amarelos_Fora_Total', 0), 'media_cartoes_amarelos_geral_1t': row.get('Media_Cartoes_Amarelos_Geral_1T', 0), 'media_cartoes_amarelos_geral_2t': row.get('Media_Cartoes_Amarelos_Geral_2T', 0), 'media_cartoes_amarelos_geral_total': row.get('Media_Cartoes_Amarelos_Geral_Total', 0),
            }
            analises_para_criar.append(AnaliseTime(**analise_data))
        AnaliseTime.objects.bulk_create(analises_para_criar)
        self.stdout.write(self.style.SUCCESS(f"{len(analises_para_criar)} análises de times importadas."))
        
        self.stdout.write(self.style.SUCCESS('PROCESSO DE IMPORTAÇÃO CONCLUÍDO!'))