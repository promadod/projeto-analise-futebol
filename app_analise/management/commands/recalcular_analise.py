# Path: app_analise/management/commands/recalcular_analise.py

from django.core.management.base import BaseCommand
from app_analise.views import recalcular_analise_completa # Importa a função que já criamos

class Command(BaseCommand):
    help = 'Força o recálculo de toda a tabela de Análise Estatística a partir dos jogos brutos existentes.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando recálculo da análise...'))
        
        try:
            recalcular_analise_completa()
            self.stdout.write(self.style.SUCCESS('Análise recalculada com sucesso!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocorreu um erro durante o recálculo: {e}'))