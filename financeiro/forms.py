from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date, timedelta

from .models import Honorario, ParcelaHonorario, Despesa, ContaBancaria
from processos.models import Processo
from clientes.models import Cliente


class HonorarioForm(forms.ModelForm):
    """
    Formulário para criação e edição de honorários
    """
    
    class Meta:
        model = Honorario
        fields = [
            'processo', 'cliente', 'tipo_cobranca', 'valor_fixo', 'valor_hora',
            'horas_trabalhadas', 'percentual_exito', 'valor_exito', 'data_vencimento',
            'forma_pagamento', 'numero_parcelas', 'observacoes'
        ]
        widgets = {
            'processo': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Selecione o processo...'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Selecione o cliente...'
            }),
            'tipo_cobranca': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleCamposCobranca()'
            }),
            'valor_fixo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00'
            }),
            'valor_hora': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00'
            }),
            'horas_trabalhadas': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.25',
                'min': '0',
                'placeholder': '0,00'
            }),
            'percentual_exito': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0,00'
            }),
            'valor_exito': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00'
            }),
            'data_vencimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'forma_pagamento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'numero_parcelas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '60',
                'value': '1'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Informações adicionais sobre o honorário...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar processos e clientes por usuário se não for staff
        if user and not user.is_staff:
            self.fields['processo'].queryset = Processo.objects.filter(
                responsavel=user
            ).select_related('cliente', 'tipo_processo')
            self.fields['cliente'].queryset = Cliente.objects.filter(
                usuario=user, ativo=True
            )
        else:
            self.fields['processo'].queryset = Processo.objects.select_related(
                'cliente', 'tipo_processo'
            )
            self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True)
        
        # Configurar data de vencimento padrão (30 dias)
        if not self.instance.pk:
            self.fields['data_vencimento'].initial = date.today() + timedelta(days=30)
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_cobranca = cleaned_data.get('tipo_cobranca')
        valor_fixo = cleaned_data.get('valor_fixo')
        valor_hora = cleaned_data.get('valor_hora')
        horas_trabalhadas = cleaned_data.get('horas_trabalhadas')
        percentual_exito = cleaned_data.get('percentual_exito')
        valor_exito = cleaned_data.get('valor_exito')
        processo = cleaned_data.get('processo')
        cliente = cleaned_data.get('cliente')
        
        # Validar campos obrigatórios por tipo de cobrança
        if tipo_cobranca == 'fixo' and not valor_fixo:
            raise ValidationError({
                'valor_fixo': _('Valor fixo é obrigatório para cobrança fixa.')
            })
        
        if tipo_cobranca == 'por_hora':
            if not valor_hora:
                raise ValidationError({
                    'valor_hora': _('Valor por hora é obrigatório para cobrança por hora.')
                })
            if not horas_trabalhadas:
                raise ValidationError({
                    'horas_trabalhadas': _('Horas trabalhadas é obrigatório para cobrança por hora.')
                })
        
        if tipo_cobranca == 'por_exito':
            if not percentual_exito:
                raise ValidationError({
                    'percentual_exito': _('Percentual de êxito é obrigatório para cobrança por êxito.')
                })
            if not valor_exito:
                raise ValidationError({
                    'valor_exito': _('Valor do êxito é obrigatório para cobrança por êxito.')
                })
        
        if tipo_cobranca == 'misto':
            if not valor_fixo and not (percentual_exito and valor_exito):
                raise ValidationError(
                    _('Para cobrança mista, informe o valor fixo e/ou percentual de êxito.')
                )
        
        # Validar se cliente e processo são compatíveis
        if processo and cliente and processo.cliente != cliente:
            raise ValidationError(
                _('O cliente selecionado deve ser o mesmo do processo.')
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Definir cliente automaticamente baseado no processo
        if instance.processo and not instance.cliente:
            instance.cliente = instance.processo.cliente
        
        if commit:
            instance.save()
            
            # Gerar parcelas se necessário
            if instance.numero_parcelas > 1:
                instance.gerar_parcelas()
        
        return instance


class ParcelaHonorarioForm(forms.ModelForm):
    """
    Formulário para edição de parcelas de honorários
    """
    
    class Meta:
        model = ParcelaHonorario
        fields = ['valor_pago', 'data_pagamento', 'status', 'observacoes']
        widgets = {
            'valor_pago': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'data_pagamento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
    
    def clean_valor_pago(self):
        valor_pago = self.cleaned_data.get('valor_pago')
        
        if valor_pago and valor_pago > self.instance.valor_parcela:
            raise ValidationError(
                _('Valor pago não pode ser maior que o valor da parcela.')
            )
        
        return valor_pago


class DespesaForm(forms.ModelForm):
    """
    Formulário para criação e edição de despesas
    """
    
    class Meta:
        model = Despesa
        fields = [
            'processo', 'tipo_despesa', 'descricao', 'valor', 'data_despesa',
            'status_reembolso', 'fornecedor', 'numero_documento', 'observacoes'
        ]
        widgets = {
            'processo': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Selecione o processo...'
            }),
            'tipo_despesa': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição detalhada da despesa...'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0,00'
            }),
            'data_despesa': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status_reembolso': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fornecedor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do fornecedor ou prestador de serviço...'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número da nota fiscal, recibo, etc...'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Informações adicionais sobre a despesa...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar processos por usuário se não for staff
        if user and not user.is_staff:
            self.fields['processo'].queryset = Processo.objects.filter(
                responsavel=user
            ).select_related('cliente', 'tipo_processo')
        else:
            self.fields['processo'].queryset = Processo.objects.select_related(
                'cliente', 'tipo_processo'
            )
        
        # Configurar data da despesa padrão (hoje)
        if not self.instance.pk:
            self.fields['data_despesa'].initial = date.today()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Definir usuário de lançamento se não estiver definido
        if not instance.usuario_lancamento_id and hasattr(self, 'user'):
            instance.usuario_lancamento = self.user
        
        if commit:
            instance.save()
        
        return instance


class ContaBancariaForm(forms.ModelForm):
    """
    Formulário para criação e edição de contas bancárias
    """
    
    class Meta:
        model = ContaBancaria
        fields = [
            'nome_conta', 'banco', 'agencia', 'numero_conta',
            'tipo_conta', 'saldo_inicial', 'ativa', 'observacoes'
        ]
        widgets = {
            'nome_conta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome identificador da conta...'
            }),
            'banco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do banco...'
            }),
            'agencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0000'
            }),
            'numero_conta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00000-0'
            }),
            'tipo_conta': forms.Select(attrs={
                'class': 'form-select'
            }),
            'saldo_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0,00'
            }),
            'ativa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Informações adicionais sobre a conta...'
            })
        }


class FiltroFinanceiroForm(forms.Form):
    """
    Formulário para filtros de relatórios financeiros
    """
    
    PERIODO_CHOICES = [
        ('', 'Selecione o período...'),
        ('hoje', 'Hoje'),
        ('ontem', 'Ontem'),
        ('esta_semana', 'Esta Semana'),
        ('semana_passada', 'Semana Passada'),
        ('este_mes', 'Este Mês'),
        ('mes_passado', 'Mês Passado'),
        ('este_ano', 'Este Ano'),
        ('ano_passado', 'Ano Passado'),
        ('personalizado', 'Período Personalizado'),
    ]
    
    periodo = forms.ChoiceField(
        choices=PERIODO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'togglePeriodoPersonalizado()'
        })
    )
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    processo = forms.ModelChoiceField(
        queryset=Processo.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-placeholder': 'Todos os processos...'
        })
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-placeholder': 'Todos os clientes...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar processos e clientes por usuário se não for staff
        if user and not user.is_staff:
            self.fields['processo'].queryset = Processo.objects.filter(
                responsavel=user
            ).select_related('cliente')
            self.fields['cliente'].queryset = Cliente.objects.filter(
                usuario=user, ativo=True
            )
        else:
            self.fields['processo'].queryset = Processo.objects.select_related('cliente')
            self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True)
    
    def clean(self):
        cleaned_data = super().clean()
        periodo = cleaned_data.get('periodo')
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if periodo == 'personalizado':
            if not data_inicio or not data_fim:
                raise ValidationError(
                    _('Para período personalizado, informe data de início e fim.')
                )
            
            if data_inicio > data_fim:
                raise ValidationError(
                    _('Data de início deve ser anterior à data de fim.')
                )
        
        return cleaned_data