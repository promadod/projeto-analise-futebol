# Path: gerador_de_analise.py
import pandas as pd

def calculate_analytics(df_jogos):
    times_unicos = pd.concat([df_jogos['Time_Casa'], df_jogos['Time_Fora']]).unique()
    ligas_unicas = df_jogos['Liga'].unique()
    lista_analise = []

    stats_base = ['Placar', 'Finalizacao', 'Chutes_no_Gol', 'Escanteios', 'Cartoes_Amarelos']
    periodos = ['1T', '2T', 'Total']

    for liga in ligas_unicas:
        for time in times_unicos:
            jogos_casa = df_jogos[(df_jogos['Time_Casa'] == time) & (df_jogos['Liga'] == liga)]
            jogos_fora = df_jogos[(df_jogos['Time_Fora'] == time) & (df_jogos['Liga'] == liga)]
            
            num_jogos_casa, num_jogos_fora = len(jogos_casa), len(jogos_fora)
            if num_jogos_casa == 0 and num_jogos_fora == 0: continue

            dados_time = {'Liga': liga, 'Time': time, 'Jogos_Casa': num_jogos_casa, 'Jogos_Fora': num_jogos_fora, 'Jogos': num_jogos_casa + num_jogos_fora}

            for stat in stats_base:
                for periodo in periodos:
                    col_casa, col_fora = f'{stat}_Casa_{periodo}', f'{stat}_Fora_{periodo}'
                    
                    soma_casa = jogos_casa[col_casa].sum()
                    dados_time[f'Media_{stat}_Casa_{periodo}'] = round(soma_casa / num_jogos_casa, 2) if num_jogos_casa > 0 else 0
                    
                    soma_fora = jogos_fora[col_fora].sum()
                    dados_time[f'Media_{stat}_Fora_{periodo}'] = round(soma_fora / num_jogos_fora, 2) if num_jogos_fora > 0 else 0
                    
                    media_geral = (soma_casa + soma_fora) / (num_jogos_casa + num_jogos_fora) if (num_jogos_casa + num_jogos_fora) > 0 else 0
                    dados_time[f'Media_{stat}_Geral_{periodo}'] = round(media_geral, 2)
            
            lista_analise.append(dados_time)

    return pd.DataFrame(lista_analise)

def main():
    try:
        df = pd.read_excel("dados_futebol_placardefutebol.xlsx", sheet_name="Estatisticas Jogos")
        print("Arquivo Excel lido com sucesso.")
    except FileNotFoundError:
        print("Erro: Arquivo 'dados_futebol_placardefutebol.xlsx' não encontrado.")
        return

    stats_base = ['Placar', 'Finalizacao', 'Chutes_no_Gol', 'Escanteios', 'Cartoes_Amarelos']
    for stat in stats_base:
        for time in ['Casa', 'Fora']:
            df[f'{stat}_{time}_Total'] = df.get(f'{stat}_{time}_1T', 0) + df.get(f'{stat}_{time}_2T', 0)
    
    print("Colunas de totais calculadas com sucesso.")
    df_analise = calculate_analytics(df)
    print("Análise estatística calculada com sucesso.")
    
    with pd.ExcelWriter("DADOS_COM_ANALISE_FINAL.xlsx", engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Estatisticas Jogos", index=False)
        df_analise.to_excel(writer, sheet_name="Analise Estatistica", index=False)
    
    print("\nArquivo 'DADOS_COM_ANALISE_FINAL.xlsx' criado com sucesso.")

if __name__ == "__main__":
    main()