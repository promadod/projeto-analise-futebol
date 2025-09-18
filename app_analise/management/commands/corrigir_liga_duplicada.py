# Path: app_analise/management/commands/corrigir_liga_duplicada.py

from django.core.management.base import BaseCommand
from app_analise.models import Liga, AnaliseTime

# --- CONFIGURAÇÃO ---
# Verifique e confirme se estes são os nomes exatos das suas ligas
# O nome que você quer que PERMANEÇA
NOME_LIGA_CORRETA = "Campeonato Brasileiro - Série B - 2025"

# O nome da liga que foi criada por engano e que você quer APAGAR
NOME_LIGA_DUPLICADA = "Brasileiro Serie B - 2025"
# --- FIM DA CONFIGURAÇÃO ---


class Command(BaseCommand):
    help = 'Move os dados de uma liga duplicada para a liga correta e apaga a duplicata.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Iniciando script de correção de liga duplicada ---'))

        try:
            # 1. Encontra as duas ligas no banco de dados
            liga_correta = Liga.objects.get(nome=NOME_LIGA_CORRETA)
            liga_duplicada = Liga.objects.get(nome=NOME_LIGA_DUPLICADA)
            self.stdout.write(f"Encontrada a liga correta: '{liga_correta.nome}'")
            self.stdout.write(f"Encontrada a liga duplicada: '{liga_duplicada.nome}'")

            # 2. Encontra todos os registros de análise que estão ligados à liga ERRADA
            analises_para_mover = AnaliseTime.objects.filter(liga=liga_duplicada)
            
            if not analises_para_mover.exists():
                self.stdout.write(self.style.WARNING(f"Nenhum dado de análise encontrado na liga duplicada '{liga_duplicada.nome}'."))
            else:
                self.stdout.write(f"Movendo {analises_para_mover.count()} registros de análise da liga duplicada para a correta...")
                # 3. Atualiza todos os registros de uma vez, apontando para a liga CORRETA
                analises_para_mover.update(liga=liga_correta)
                self.stdout.write(self.style.SUCCESS("Dados movidos com sucesso!"))

            # 4. Apaga a liga duplicada, que agora está vazia e segura para ser removida
            self.stdout.write(f"Apagando a liga duplicada '{liga_duplicada.nome}'...")
            liga_duplicada.delete()
            self.stdout.write(self.style.SUCCESS("Liga duplicada apagada com sucesso."))
            
            self.stdout.write(self.style.SUCCESS("\n--- CORREÇÃO CONCLUÍDA ---"))

        except Liga.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"ERRO: Uma das ligas ('{NOME_LIGA_CORRETA}' ou '{NOME_LIGA_DUPLICADA}') não foi encontrada. Verifique os nomes na configuração do script."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ocorreu um erro inesperado: {e}"))