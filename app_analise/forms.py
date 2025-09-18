from django import forms
from .models import Liga, Time, Jogo
from .models import Aposta,Banca

class BancaForm(forms.ModelForm):
    class Meta:
        model = Banca
        fields = ['nome', 'valor_inicial']

class ApostaForm(forms.ModelForm):
    # Definimos o campo aqui para filtrar apenas as bancas ativas
    banca = forms.ModelChoiceField(
        queryset=Banca.objects.filter(ativa=True),
        label="Banca",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Selecione uma banca ativa"
    )

    class Meta:
        model = Aposta
        # A 'banca' já foi definida acima, o resto vem do model
        fields = [
            'banca', 'data', 'evento', 'mercado', 
            'odd', 'valor_apostado', 'resultado', 
            'is_multipla', 'detalhes_multipla'
        ]
        
        # Widgets para estilização com Bootstrap
        widgets = {
            'data': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'evento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Flamengo vs Palmeiras', 'maxlength': '80'}),
            'mercado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Mais de 2.5 Gols'}),
            'odd': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1.85'}),
            'valor_apostado': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 10.00'}),
            'resultado': forms.Select(attrs={'class': 'form-select'}),
            'is_multipla': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'detalhes_multipla': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class LigaForm(forms.ModelForm):
    class Meta:
        model = Liga
        fields = ['nome']

class TimeForm(forms.ModelForm):
    class Meta:
        model = Time
        fields = ['liga', 'nome']

class JogoForm(forms.ModelForm):
    class Meta:
        model = Jogo
        fields = '__all__'
        exclude = ['id_jogo']

        # --- ADICIONADO AQUI PARA O SELECIONADOR DE DATA ---
        widgets = {
            'data': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'rodada': forms.TextInput(attrs={'class': 'form-control'}),
            'placar_casa': forms.NumberInput(attrs={'class': 'form-control'}),
            'placar_fora': forms.NumberInput(attrs={'class': 'form-control'}),
            'finalizacao_casa': forms.NumberInput(attrs={'class': 'form-control'}),
            'finalizacao_fora': forms.NumberInput(attrs={'class': 'form-control'}),
            'chutes_no_gol_casa': forms.NumberInput(attrs={'class': 'form-control'}),
            'chutes_no_gol_fora': forms.NumberInput(attrs={'class': 'form-control'}),
            'escanteios_casa': forms.NumberInput(attrs={'class': 'form-control'}),
            'escanteios_fora': forms.NumberInput(attrs={'class': 'form-control'}),
            'cartoes_amarelos_casa': forms.NumberInput(attrs={'class': 'form-control'}),
            'cartoes_amarelos_fora': forms.NumberInput(attrs={'class': 'form-control'}),
            'cartoes_vermelhos_casa': forms.NumberInput(attrs={'class': 'form-control'}),
            'cartoes_vermelhos_fora': forms.NumberInput(attrs={'class': 'form-control'}),
            'liga': forms.Select(attrs={'class': 'form-select'}),
            'time_casa': forms.Select(attrs={'class': 'form-select'}),
            'time_fora': forms.Select(attrs={'class': 'form-select'}),
        }
        # --- FIM DA ADIÇÃO ---

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['time_casa'].queryset = Time.objects.none()
        self.fields['time_fora'].queryset = Time.objects.none()

        if 'liga' in self.data:
            try:
                liga_id = int(self.data.get('liga'))
                self.fields['time_casa'].queryset = Time.objects.filter(liga_id=liga_id).order_by('nome')
                self.fields['time_fora'].queryset = Time.objects.filter(liga_id=liga_id).order_by('nome')
            except (ValueError, TypeError):
                pass


class ApostaForm(forms.ModelForm):
    # CORREÇÃO: Adicionamos um campo explícito para a banca
    # Isso cria um dropdown listando apenas as bancas ativas
    banca = forms.ModelChoiceField(
        queryset=Banca.objects.filter(ativa=True),
        label="Banca",
        empty_label="Selecione uma banca"
    )

    class Meta:
        model = Aposta
        # Adicionamos 'banca' à lista de campos
        fields = ['banca', 'data', 'evento', 'mercado', 'odd', 'valor_apostado', 'resultado']
        widgets = {
            'data': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data'].input_formats = ('%Y-%m-%dT%H:%M',)
