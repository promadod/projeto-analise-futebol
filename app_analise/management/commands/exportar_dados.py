# Path: gerador_de_analise.py
# OBJETIVO: Ler um arquivo com dados brutos e gerar a aba de análise estatística.

import pandas as pd
import unicodedata

# --- 1. CONFIGURAÇÃO ---
# Coloque aqui o nome do seu arquivo Excel com os dados brutos da Série A
ARQUIVO_DE_ENTRADA = 'DADOS_SERIE_A_BRUTO.xlsx'

# Nome do novo arquivo final que será gerado com a análise
ARQUIVO_DE_SAIDA = 'RELATORIO_SERIE_A_COM_ANALISE.xlsx'
# --- FIM DA CONFIGURAÇÃO ---


def remover_acentos(texto):
    if not isinstance(texto, str): return texto
    nfkd_form = unicodedata.normalize('NFD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def calculate_analytics(df):
    print("Calculando a análise estatística completa...")
    stats_map = {
        'Finalizacoes': ('Finalizacao_Casa', 'Finalizacao_Fora'),
        'Chutes_no_Gol': ('Chutes_no_Gol_Casa', 'Chutes_no_Gol_Fora'),
        'Escanteios': ('Escanteios_Casa', 'Escanteios_Fora'),
        'Cartoes_Amarelos': ('Cartoes_Amarelos_Casa', 'Cartoes_Amarelos_Fora'),
        'Cartoes_Vermelhos': ('Cartoes_Vermelhos_Casa', 'Cartoes_Vermelhos_Fora'),
    }
    analytics_rows = []
    
    for stat_group in stats_map.values():
        for col in stat_group:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Time_Casa'] = df['Time_Casa'].astype(str).apply(remover_acentos).str.strip().str.title()
    df['Time_Fora'] = df['Time_Fora'].astype(str).apply(remover_acentos).str.strip().str.title()
    df['Liga'] = df['Liga'].astype(str).str.strip()

    for liga in sorted(df['Liga'].unique()):
        df_liga = df[df['Liga'] == liga]
        all_teams = sorted(list(pd.concat([df_liga['Time_Casa'], df_liga['Time_Fora']]).unique()))
        
        for team in all_teams:
            if pd.isna(team) or team in ['nan', '']: continue
            
            team_stats = {'Liga': liga, 'Time': team}
            jogos_casa_df = df_liga[df_liga['Time_Casa'] == team]
            jogos_fora_df = df_liga[df_liga['Time_Fora'] == team]
            contagem_casa, contagem_fora = len(jogos_casa_df), len(jogos_fora_df)
            jogos_total = contagem_casa + contagem_fora
            team_stats.update({'Jogos_Casa': contagem_casa, 'Jogos_Fora': contagem_fora, 'Jogos_Total': jogos_total})
            
            for base_name, (col_casa, col_fora) in stats_map.items():
                total_casa = jogos_casa_df[col_casa].sum() if col_casa in jogos_casa_df.columns else 0
                media_casa = round(total_casa / contagem_casa, 2) if contagem_casa > 0 else 0
                team_stats.update({f'Total_{base_name}_Casa': total_casa, f'Media_{base_name}_Casa': media_casa})

                total_fora = jogos_fora_df[col_fora].sum() if col_fora in jogos_fora_df.columns else 0
                media_fora = round(total_fora / contagem_fora, 2) if contagem_fora > 0 else 0
                team_stats.update({f'Total_{base_name}_Fora': total_fora, f'Media_{base_name}_Fora': media_fora})

                total_geral = total_casa + total_fora
                media_geral = round(total_geral / jogos_total, 2) if jogos_total > 0 else 0
                team_stats.update({f'Total_{base_name}_Geral': total_geral, f'Media_{base_name}_Geral': media_geral})
            
            analytics_rows.append(team_stats)
            
    return pd.DataFrame(analytics_rows)

def main():
    print(f"--- Iniciando Geração de Análise para o arquivo '{ARQUIVO_DE_ENTRADA}' ---")
    try:
        # Lê a aba de dados brutos do seu arquivo
        df_bruto = pd.read_excel(ARQUIVO_DE_ENTRADA, sheet_name='Estatisticas Jogos')
        print(f"Arquivo carregado com {len(df_bruto)} jogos.")
        
    except Exception as e:
        print(f"ERRO: Não foi possível ler o arquivo '{ARQUIVO_DE_ENTRADA}'. Verifique o nome do arquivo e da aba 'Estatisticas Jogos'. Erro: {e}")
        return

    # Calcula a aba de análise a partir dos dados brutos
    df_analise = calculate_analytics(df_bruto.copy())
    
    # Salva um NOVO arquivo com as duas abas
    with pd.ExcelWriter(ARQUIVO_DE_SAIDA, engine='xlsxwriter') as writer:
        df_bruto.to_excel(writer, sheet_name='Estatisticas Jogos', index=False)
        
        # Formata as médias antes de salvar
        for col in df_analise.columns:
            if 'Media_' in col:
                df_analise[col] = df_analise[col].apply(lambda x: f'{x:.2f}'.replace('.', ','))
        df_analise.to_excel(writer, sheet_name='Analise Estatistica', index=False)
    
    print(f"\nPROCESSO CONCLUÍDO. Novo arquivo '{ARQUIVO_DE_SAIDA}' foi criado com sucesso.")
    print("Ele contém seus dados brutos e a aba de análise completa.")

if __name__ == '__main__':
    main()