# Path: app_analise/models.py (VERSÃO CORRIGIDA)

from django.db import models
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal


class Liga(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Liga")

    def __str__(self):
        return self.nome

class Time(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Time")
    liga = models.ForeignKey(Liga, on_delete=models.CASCADE, related_name='times', verbose_name="Liga")

    def __str__(self):
        return self.nome

class Jogo(models.Model):
    liga = models.ForeignKey(Liga, on_delete=models.CASCADE, verbose_name="Liga")
    rodada = models.IntegerField(verbose_name="Rodada", default=0)
    data = models.DateField(verbose_name="Data do Jogo", default=timezone.now)
    time_casa = models.ForeignKey(Time, on_delete=models.CASCADE, related_name='jogos_casa', verbose_name="Time da Casa")
    time_fora = models.ForeignKey(Time, on_delete=models.CASCADE, related_name='jogos_fora', verbose_name="Time de Fora")

    # Estatísticas do 1º Tempo
    placar_casa_1t = models.IntegerField(default=0, verbose_name="Placar Casa 1T")
    placar_fora_1t = models.IntegerField(default=0, verbose_name="Placar Fora 1T")
    finalizacao_casa_1t = models.IntegerField(default=0, verbose_name="Finalizações Casa 1T")
    finalizacao_fora_1t = models.IntegerField(default=0, verbose_name="Finalizações Fora 1T")
    chutes_no_gol_casa_1t = models.IntegerField(default=0, verbose_name="Chutes no Gol Casa 1T")
    chutes_no_gol_fora_1t = models.IntegerField(default=0, verbose_name="Chutes no Gol Fora 1T")
    escanteios_casa_1t = models.IntegerField(default=0, verbose_name="Escanteios Casa 1T")
    escanteios_fora_1t = models.IntegerField(default=0, verbose_name="Escanteios Fora 1T")
    cartoes_amarelos_casa_1t = models.IntegerField(default=0, verbose_name="Cartões Amarelos Casa 1T")
    cartoes_amarelos_fora_1t = models.IntegerField(default=0, verbose_name="Cartões Amarelos Fora 1T")

    # Estatísticas do 2º Tempo
    placar_casa_2t = models.IntegerField(default=0, verbose_name="Placar Casa 2T")
    placar_fora_2t = models.IntegerField(default=0, verbose_name="Placar Fora 2T")
    finalizacao_casa_2t = models.IntegerField(default=0, verbose_name="Finalizações Casa 2T")
    finalizacao_fora_2t = models.IntegerField(default=0, verbose_name="Finalizações Fora 2T")
    chutes_no_gol_casa_2t = models.IntegerField(default=0, verbose_name="Chutes no Gol Casa 2T")
    chutes_no_gol_fora_2t = models.IntegerField(default=0, verbose_name="Chutes no Gol Fora 2T")
    escanteios_casa_2t = models.IntegerField(default=0, verbose_name="Escanteios Casa 2T")
    escanteios_fora_2t = models.IntegerField(default=0, verbose_name="Escanteios Fora 2T")
    cartoes_amarelos_casa_2t = models.IntegerField(default=0, verbose_name="Cartões Amarelos Casa 2T")
    cartoes_amarelos_fora_2t = models.IntegerField(default=0, verbose_name="Cartões Amarelos Fora 2T")

    # Totais (Armazenados para facilitar consultas)
    placar_casa_total = models.IntegerField(default=0)
    placar_fora_total = models.IntegerField(default=0)
    finalizacao_casa_total = models.IntegerField(default=0)
    finalizacao_fora_total = models.IntegerField(default=0)
    chutes_no_gol_casa_total = models.IntegerField(default=0)
    chutes_no_gol_fora_total = models.IntegerField(default=0)
    escanteios_casa_total = models.IntegerField(default=0)
    escanteios_fora_total = models.IntegerField(default=0)
    cartoes_amarelos_casa_total = models.IntegerField(default=0)
    cartoes_amarelos_fora_total = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.time_casa} vs {self.time_fora} em {self.data}"

class AnaliseTime(models.Model):
    time = models.OneToOneField(Time, on_delete=models.CASCADE, primary_key=True)
    liga = models.ForeignKey(Liga, on_delete=models.CASCADE, null=True, blank=True)
    
    # Contagem de jogos
    jogos_casa = models.IntegerField(default=0)
    jogos_fora = models.IntegerField(default=0)
    jogos = models.IntegerField(default=0)

    # --- Médias de Placar ---
    media_placar_casa_1t = models.FloatField(default=0.0)
    media_placar_fora_1t = models.FloatField(default=0.0)
    media_placar_geral_1t = models.FloatField(default=0.0)
    media_placar_casa_2t = models.FloatField(default=0.0)
    media_placar_fora_2t = models.FloatField(default=0.0)
    media_placar_geral_2t = models.FloatField(default=0.0)
    media_placar_casa_total = models.FloatField(default=0.0)
    media_placar_fora_total = models.FloatField(default=0.0)
    media_placar_geral_total = models.FloatField(default=0.0)

    # --- Médias de Finalização ---
    media_finalizacao_casa_1t = models.FloatField(default=0.0)
    media_finalizacao_fora_1t = models.FloatField(default=0.0)
    media_finalizacao_geral_1t = models.FloatField(default=0.0)
    media_finalizacao_casa_2t = models.FloatField(default=0.0)
    media_finalizacao_fora_2t = models.FloatField(default=0.0)
    media_finalizacao_geral_2t = models.FloatField(default=0.0)
    media_finalizacao_casa_total = models.FloatField(default=0.0)
    media_finalizacao_fora_total = models.FloatField(default=0.0)
    media_finalizacao_geral_total = models.FloatField(default=0.0)

    # --- Médias de Chutes no Gol ---
    media_chutes_no_gol_casa_1t = models.FloatField(default=0.0)
    media_chutes_no_gol_fora_1t = models.FloatField(default=0.0)
    media_chutes_no_gol_geral_1t = models.FloatField(default=0.0)
    media_chutes_no_gol_casa_2t = models.FloatField(default=0.0)
    media_chutes_no_gol_fora_2t = models.FloatField(default=0.0)
    media_chutes_no_gol_geral_2t = models.FloatField(default=0.0)
    media_chutes_no_gol_casa_total = models.FloatField(default=0.0)
    media_chutes_no_gol_fora_total = models.FloatField(default=0.0)
    media_chutes_no_gol_geral_total = models.FloatField(default=0.0)

    # --- Médias de Escanteios ---
    media_escanteios_casa_1t = models.FloatField(default=0.0)
    media_escanteios_fora_1t = models.FloatField(default=0.0)
    media_escanteios_geral_1t = models.FloatField(default=0.0)
    media_escanteios_casa_2t = models.FloatField(default=0.0)
    media_escanteios_fora_2t = models.FloatField(default=0.0)
    media_escanteios_geral_2t = models.FloatField(default=0.0)
    media_escanteios_casa_total = models.FloatField(default=0.0)
    media_escanteios_fora_total = models.FloatField(default=0.0)
    media_escanteios_geral_total = models.FloatField(default=0.0)

    # --- Médias de Cartões Amarelos ---
    media_cartoes_amarelos_casa_1t = models.FloatField(default=0.0)
    media_cartoes_amarelos_fora_1t = models.FloatField(default=0.0)
    media_cartoes_amarelos_geral_1t = models.FloatField(default=0.0)
    media_cartoes_amarelos_casa_2t = models.FloatField(default=0.0)
    media_cartoes_amarelos_fora_2t = models.FloatField(default=0.0)
    media_cartoes_amarelos_geral_2t = models.FloatField(default=0.0)
    media_cartoes_amarelos_casa_total = models.FloatField(default=0.0)
    media_cartoes_amarelos_fora_total = models.FloatField(default=0.0)
    media_cartoes_amarelos_geral_total = models.FloatField(default=0.0)

    def __str__(self):
        return f"Estatísticas de {self.time.nome}"

class Banca(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Banca")
    valor_inicial = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Inicial (R$)")
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class Aposta(models.Model):
    # Adicionamos a relação com a Banca
    banca = models.ForeignKey(Banca, on_delete=models.CASCADE, related_name='apostas')

    RESULTADO_CHOICES = [ ('GREEN', 'Green'), ('RED', 'Red'), ('VOID', 'Anulada'), ('PENDING', 'Pendente'), ]
    data = models.DateTimeField(default=timezone.now, verbose_name="Data da Aposta")
    evento = models.CharField(max_length=80, verbose_name="Evento Esportivo")
    mercado = models.CharField(max_length=100, verbose_name="Mercado/Tipo de Aposta")
    odd = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Odd")
    valor_apostado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Apostado (R$)")
    resultado = models.CharField(max_length=10, choices=RESULTADO_CHOICES, default='PENDING')
    retorno = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Lucro/Prejuízo (R$)", blank=True)
    is_multipla = models.BooleanField(default=False, verbose_name="É uma aposta múltipla?")
    detalhes_multipla = models.TextField(blank=True, null=True, verbose_name="Detalhes da Múltipla")

    def __str__(self):
        return f"{self.evento} ({self.get_resultado_display()})"

    def save(self, *args, **kwargs):
        if self.resultado == 'GREEN':
            self.retorno = (self.valor_apostado * self.odd) - self.valor_apostado
        elif self.resultado == 'RED':
            self.retorno = -self.valor_apostado
        else:
            self.retorno = 0.00
        super().save(*args, **kwargs)

class Configuracao(models.Model):
    # CORREÇÃO: Usar string para o default de DecimalField é a melhor prática
    banca_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('250.00'))

    def __str__(self):
        return f"Configuração da Banca (Inicial: R${self.banca_inicial})"