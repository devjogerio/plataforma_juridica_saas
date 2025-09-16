from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Alerta, ConfiguracaoAlerta, TipoAlerta, PrioridadeAlerta, StatusAlerta


class AlertaForm(forms.ModelForm):
    """Formulário para criação e edição de alertas"""
    
    class Meta:
        model = Alerta
        fields = [
            'titulo', 'descricao', 'tipo', 'prioridade', 'data_alerta',
            'data_vencimento', 'antecedencia_minutos', 'recorrente',
            'frequencia_recorrencia', 'notificar_email', 'url_acao'
        ]
        
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o título do alerta'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição detalhada do alerta (opcional)'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'prioridade': forms.Select(attrs={
                'class': 'form-select'
            }),
            'data_alerta': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'data_vencimento': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'antecedencia_minutos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '5'
            }),
            'recorrente': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'frequencia_recorrencia': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notificar_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'url_acao': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://exemplo.com/acao'
            }),
        }
        
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
            'tipo': 'Tipo de Alerta',
            'prioridade': 'Prioridade',
            'data_alerta': 'Data e Hora do Alerta',
            'data_vencimento': 'Data de Vencimento',
            'antecedencia_minutos': 'Antecedência (minutos)',
            'recorrente': 'Alerta Recorrente',
            'frequencia_recorrencia': 'Frequência',
            'notificar_email': 'Notificar por Email',
            'url_acao': 'URL de Ação',
        }
        
        help_texts = {
            'data_alerta': 'Quando o alerta deve ser disparado',
            'data_vencimento': 'Data limite para a ação (opcional)',
            'antecedencia_minutos': 'Quantos minutos antes disparar o alerta',
            'recorrente': 'Marque se o alerta deve se repetir',
            'frequencia_recorrencia': 'Com que frequência o alerta deve se repetir',
            'notificar_email': 'Enviar notificação por email',
            'url_acao': 'Link para onde o usuário será direcionado (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurações específicas para campos
        self.fields['frequencia_recorrencia'].required = False
        
        # Se não for recorrente, esconder frequência
        if not self.instance.pk or not self.instance.recorrente:
            self.fields['frequencia_recorrencia'].widget.attrs['style'] = 'display: none;'
    
    def clean_data_alerta(self):
        """Valida a data do alerta"""
        data_alerta = self.cleaned_data.get('data_alerta')
        
        if data_alerta and data_alerta <= timezone.now():
            raise ValidationError('A data do alerta deve ser no futuro.')
        
        return data_alerta
    
    def clean_data_vencimento(self):
        """Valida a data de vencimento"""
        data_vencimento = self.cleaned_data.get('data_vencimento')
        data_alerta = self.cleaned_data.get('data_alerta')
        
        if data_vencimento and data_alerta and data_vencimento < data_alerta:
            raise ValidationError('A data de vencimento não pode ser anterior à data do alerta.')
        
        return data_vencimento
    
    def clean(self):
        """Validações gerais do formulário"""
        cleaned_data = super().clean()
        recorrente = cleaned_data.get('recorrente')
        frequencia_recorrencia = cleaned_data.get('frequencia_recorrencia')
        
        if recorrente and not frequencia_recorrencia:
            raise ValidationError({
                'frequencia_recorrencia': 'Frequência é obrigatória para alertas recorrentes.'
            })
        
        return cleaned_data


class AlertaFiltroForm(forms.Form):
    """Formulário para filtros na listagem de alertas"""
    
    STATUS_CHOICES = [('', 'Todos')] + list(StatusAlerta.choices)
    TIPO_CHOICES = [('', 'Todos')] + list(TipoAlerta.choices)
    PRIORIDADE_CHOICES = [('', 'Todas')] + list(PrioridadeAlerta.choices)
    PERIODO_CHOICES = [
        ('', 'Todos'),
        ('hoje', 'Hoje'),
        ('amanha', 'Amanhã'),
        ('semana', 'Próximos 7 dias'),
        ('mes', 'Próximos 30 dias'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    prioridade = forms.ChoiceField(
        choices=PRIORIDADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    periodo = forms.ChoiceField(
        choices=PERIODO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    busca = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título ou descrição...'
        })
    )


class ConfiguracaoAlertaForm(forms.ModelForm):
    """Formulário para configurações de alertas do usuário"""
    
    class Meta:
        model = ConfiguracaoAlerta
        fields = [
            'alertas_ativos', 'alertas_prazos', 'alertas_audiencias',
            'alertas_reunioes', 'alertas_pagamentos', 'alertas_tarefas',
            'notificacao_email', 'notificacao_push', 'antecedencia_padrao',
            'horario_inicio', 'horario_fim', 'alertas_fins_semana'
        ]
        
        widgets = {
            'alertas_ativos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'alertas_prazos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'alertas_audiencias': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'alertas_reunioes': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'alertas_pagamentos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'alertas_tarefas': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notificacao_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notificacao_push': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'antecedencia_padrao': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '5',
                'step': '5'
            }),
            'horario_inicio': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'horario_fim': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'alertas_fins_semana': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'alertas_ativos': 'Alertas Ativos',
            'alertas_prazos': 'Alertas de Prazos',
            'alertas_audiencias': 'Alertas de Audiências',
            'alertas_reunioes': 'Alertas de Reuniões',
            'alertas_pagamentos': 'Alertas de Pagamentos',
            'alertas_tarefas': 'Alertas de Tarefas',
            'notificacao_email': 'Notificações por Email',
            'notificacao_push': 'Notificações Push',
            'antecedencia_padrao': 'Antecedência Padrão (minutos)',
            'horario_inicio': 'Horário de Início',
            'horario_fim': 'Horário de Fim',
            'alertas_fins_semana': 'Alertas nos Fins de Semana',
        }
        
        help_texts = {
            'alertas_ativos': 'Ativar/desativar todos os alertas',
            'antecedencia_padrao': 'Antecedência padrão para novos alertas',
            'horario_inicio': 'Não enviar alertas antes deste horário',
            'horario_fim': 'Não enviar alertas após este horário',
            'alertas_fins_semana': 'Receber alertas nos sábados e domingos',
        }
    
    def clean_horario_fim(self):
        """Valida se o horário de fim é posterior ao de início"""
        horario_inicio = self.cleaned_data.get('horario_inicio')
        horario_fim = self.cleaned_data.get('horario_fim')
        
        if horario_inicio and horario_fim and horario_fim <= horario_inicio:
            raise ValidationError('O horário de fim deve ser posterior ao horário de início.')
        
        return horario_fim


class AdiarAlertaForm(forms.Form):
    """Formulário para adiar um alerta"""
    
    nova_data = forms.DateTimeField(
        label='Nova Data e Hora',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        help_text='Selecione a nova data e hora para o alerta'
    )
    
    def clean_nova_data(self):
        """Valida se a nova data é no futuro"""
        nova_data = self.cleaned_data.get('nova_data')
        
        if nova_data and nova_data <= timezone.now():
            raise ValidationError('A nova data deve ser no futuro.')
        
        return nova_data


class AlertaRapidoForm(forms.Form):
    """Formulário simplificado para criação rápida de alertas"""
    
    titulo = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o título do alerta'
        })
    )
    
    data_alerta = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    tipo = forms.ChoiceField(
        choices=TipoAlerta.choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    prioridade = forms.ChoiceField(
        choices=PrioridadeAlerta.choices,
        initial=PrioridadeAlerta.MEDIA,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean_data_alerta(self):
        """Valida a data do alerta"""
        data_alerta = self.cleaned_data.get('data_alerta')
        
        if data_alerta and data_alerta <= timezone.now():
            raise ValidationError('A data do alerta deve ser no futuro.')
        
        return data_alerta