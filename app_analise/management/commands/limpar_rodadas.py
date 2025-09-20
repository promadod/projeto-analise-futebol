import re
from django.core.management.base import BaseCommand
from app_analise.models import Jogo

class Command(BaseCommand):
    help = 'Limpa e converte o campo de rodada de todos os jogos, removendo textos e caracteres especiais.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando limpeza do campo "rodada"...'))
        
        jogos_para_corrigir = Jogo.objects.all()
        jogos_corrigidos = 0

        for jogo in jogos_para_corrigir:
            try:
                # Tenta converter o valor atual para inteiro. Se já for, pula para o próximo.
                int(jogo.rodada)
                continue
            except (ValueError, TypeError):
                # Se não for um inteiro, prossegue com a limpeza
                valor_antigo = str(jogo.rodada)
                
                # Usa uma expressão regular para extrair apenas os números do texto
                numeros = re.findall(r'\d+', valor_antigo)
                
                if numeros:
                    # Pega o primeiro número encontrado e converte para inteiro
                    novo_valor_rodada = int(numeros[0])
                    
                    self.stdout.write(f'Corrigindo Jogo ID {jogo.id}: de "{valor_antigo}" para "{novo_valor_rodada}"')
                    jogo.rodada = novo_valor_rodada
                    jogo.save()
                    jogos_corrigidos += 1
                else:
                    # Caso não encontre nenhum número, define como 0 (ou outro padrão)
                    self.stdout.write(self.style.WARNING(f'AVISO: Jogo ID {jogo.id} com rodada inválida ("{valor_antigo}"). Definindo para 0.'))
                    jogo.rodada = 0
                    jogo.save()
                    jogos_corrigidos += 1

        self.stdout.write(self.style.SUCCESS(f'Limpeza concluída! {jogos_corrigidos} jogos foram atualizados.'))