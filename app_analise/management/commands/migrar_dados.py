import pandas as pd
from sqlalchemy import create_engine
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Migra dados diretamente do SQLite para o PostgreSQL usando Pandas.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando migração de dados...'))

        # --- Configurações dos Bancos de Dados ---
        # Assume que você tem uma configuração para 'sqlite' e 'default' (postgresql) no settings.py

        # Conexão com o banco de dados de ORIGEM (SQLite)
        db_path_sqlite = settings.DATABASES['default']['NAME']
        engine_sqlite = create_engine(f'sqlite:///{db_path_sqlite}')

        # Conexão com o banco de dados de DESTINO (PostgreSQL)
        db_conf_pg = settings.DATABASES['postgresql'] # <<< USA A NOVA CONFIGURAÇÃO
        conn_str_pg = f"postgresql://{db_conf_pg['USER']}:{db_conf_pg['PASSWORD']}@{db_conf_pg['HOST']}:{db_conf_pg['PORT']}/{db_conf_pg['NAME']}"
        engine_pg = create_engine(conn_str_pg)

        # --- Lista de todas as tabelas do seu app para migrar ---
        # (Verifique se os nomes das tabelas estão corretos)
        tabelas_para_migrar = [
            'app_analise_liga',
            'app_analise_time',
            'app_analise_banca',
            'app_analise_aposta',
            'app_analise_jogo',
            'app_analise_analisetime',
        ]

        self.stdout.write(self.style.WARNING('Lendo dados do SQLite...'))

        for tabela in tabelas_para_migrar:
            try:
                # Lê a tabela inteira do SQLite para um DataFrame do Pandas
                df = pd.read_sql_table(tabela, engine_sqlite)
                self.stdout.write(f'  - Lidos {len(df)} registros da tabela {tabela}.')

                # Escreve o DataFrame diretamente na tabela correspondente no PostgreSQL
                # 'replace' apaga a tabela antiga e a substitui com os novos dados
                df.to_sql(tabela, engine_pg, if_exists='append', index=False)
                self.stdout.write(self.style.SUCCESS(f'  - Dados da tabela {tabela} migrados com sucesso para o PostgreSQL!'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ERRO ao migrar a tabela {tabela}: {e}'))

        self.stdout.write(self.style.SUCCESS('Migração de dados concluída!'))