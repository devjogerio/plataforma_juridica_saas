from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date, timedelta

from .models import Honorario, ParcelaHonorario, Despesa, ContaBancaria, DocumentoHonorario
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
            ).select_related('cliente')
            self.fields['cliente'].queryset = Cliente.objects.filter(
                usuario=user, ativo=True
            )
        else:
            self.fields['processo'].queryset = Processo.objects.select_related(
                'cliente'
            )
            self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True)
        
        # Configurar data de vencimento padrão (30 dias)
        if not self.instance.pk:
            self.fields['data_vencimento'].initial = date.today() + timedelta(days=30)
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


class DocumentoHonorarioForm(forms.ModelForm):
    """
    Formulário para upload de documentos de honorários
    """
    
    class Meta:
        model = DocumentoHonorario
        fields = ['arquivo', 'tipo_documento', 'descricao']
        widgets = {
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif',
                'data-max-size': '10485760'  # 10MB em bytes
            }),
            'tipo_documento': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva o conteúdo do documento (opcional)...'
            })
        }
    
    def clean_arquivo(self):
        """Valida o arquivo enviado"""
        arquivo = self.cleaned_data.get('arquivo')
        
        if arquivo:
            # Verificar tamanho do arquivo (máximo 10MB)
            if arquivo.size > 10 * 1024 * 1024:
                raise ValidationError(
                    _('O arquivo é muito grande. Tamanho máximo permitido: 10MB.')
                )
            
            # Verificar extensão do arquivo
            nome_arquivo = arquivo.name.lower()
            extensoes_permitidas = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif']
            
            if not any(nome_arquivo.endswith(ext) for ext in extensoes_permitidas):
                raise ValidationError(
                    _('Tipo de arquivo não permitido. Formatos aceitos: PDF, DOC, DOCX, JPG, PNG, GIF.')
                )
        
        return arquivo
    
    def save(self, commit=True):
        """Salva o documento com informações adicionais"""
        documento = super().save(commit=False)
        
        if self.cleaned_data.get('arquivo'):
            documento.nome_arquivo = self.cleaned_data['arquivo'].name
        
        if commit:
            documento.save()
        
        return documento


class HonorarioPrimeiroForm(forms.ModelForm):
    """
    Formulário específico para criação do primeiro honorário.
    Inclui validações especiais e orientações para novos usuários.
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
                'class': 'form-select primeiro-honorario-field',
                'data-placeholder': 'Selecione o processo...',
                'required': True
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select primeiro-honorario-field',
                'data-placeholder': 'Selecione o cliente...',
                'required': True
            }),
            'tipo_cobranca': forms.Select(attrs={
                'class': 'form-select primeiro-honorario-field',
                'onchange': 'toggleCamposCobrancaPrimeiro()',
                'required': True
            }),
            'valor_fixo': forms.NumberInput(attrs={
                'class': 'form-control primeiro-honorario-field',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0,00',
                'data-currency': 'true'
            }),
            'valor_hora': forms.NumberInput(attrs={
                'class': 'form-control primeiro-honorario-field',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0,00',
                'data-currency': 'true'
            }),
            'horas_trabalhadas': forms.NumberInput(attrs={
                'class': 'form-control primeiro-honorario-field',
                'step': '0.25',
                'min': '0.25',
                'placeholder': '0,00'
            }),
            'percentual_exito': forms.NumberInput(attrs={
                'class': 'form-control primeiro-honorario-field',
                'step': '0.01',
                'min': '0.01',
                'max': '100',
                'placeholder': '0,00'
            }),
            'valor_exito': forms.NumberInput(attrs={
                'class': 'form-control primeiro-honorario-field',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0,00',
                'data-currency': 'true'
            }),
            'data_vencimento': forms.DateInput(attrs={
                'class': 'form-control primeiro-honorario-field',
                'type': 'date',
                'required': True
            }),
            'forma_pagamento': forms.Select(attrs={
                'class': 'form-select primeiro-honorario-field',
                'required': True
            }),
            'numero_parcelas': forms.NumberInput(attrs={
                'class': 'form-control primeiro-honorario-field',
                'min': '1',
                'max': '60',
                'value': '1'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control primeiro-honorario-field',
                'rows': 4,
                'placeholder': 'Descreva detalhes importantes sobre este honorário...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar processos e clientes por usuário
        if user and not user.is_staff:
            self.fields['processo'].queryset = Processo.objects.filter(
                usuario_responsavel=user
            ).select_related('cliente')
            self.fields['cliente'].queryset = Cliente.objects.filter(
                usuario=user, ativo=True
            )
        else:
            self.fields['processo'].queryset = Processo.objects.select_related(
                'cliente'
            )
            self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True)
        
        # Configurar data de vencimento padrão (30 dias)
        if not self.instance.pk:
            self.fields['data_vencimento'].initial = date.today() + timedelta(days=30)
        
        # Tornar campos obrigatórios para primeiro honorário
        self.fields['processo'].required = True
        self.fields['cliente'].required = True
        self.fields['tipo_cobranca'].required = True
        self.fields['data_vencimento'].required = True
        self.fields['forma_pagamento'].required = True
        
        # Adicionar help texts específicos
        self.fields['tipo_cobranca'].help_text = (
            "Escolha como será calculado o valor do honorário. "
            "Para iniciantes, recomendamos 'Valor Fixo'."
        )
        self.fields['valor_fixo'].help_text = (
            "Valor total do honorário em reais. Ex: R$ 1.500,00"
        )
        self.fields['data_vencimento'].help_text = (
            "Data limite para pagamento do honorário"
        )
        self.fields['numero_parcelas'].help_text = (
            "Número de parcelas para dividir o pagamento (máximo 60)"
        )
    
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
        data_vencimento = cleaned_data.get('data_vencimento')
        
        # Validações específicas para primeiro honorário
        if not processo:
            raise ValidationError({
                'processo': _('Selecione um processo para este honorário.')
            })
        
        if not cliente:
            raise ValidationError({
                'cliente': _('Selecione um cliente para este honorário.')
            })
        
        if not data_vencimento:
            raise ValidationError({
                'data_vencimento': _('Defina uma data de vencimento.')
            })
        
        # Validar data de vencimento não pode ser no passado
        if data_vencimento and data_vencimento < date.today():
            raise ValidationError({
                'data_vencimento': _('A data de vencimento não pode ser no passado.')
            })
        
        # Validar campos obrigatórios por tipo de cobrança com mensagens específicas
        if tipo_cobranca == 'fixo':
            if not valor_fixo:
                raise ValidationError({
                    'valor_fixo': _('Para cobrança fixa, informe o valor total do honorário.')
                })
            if valor_fixo <= 0:
                raise ValidationError({
                    'valor_fixo': _('O valor do honorário deve ser maior que zero.')
                })
        
        elif tipo_cobranca == 'por_hora':
            if not valor_hora:
                raise ValidationError({
                    'valor_hora': _('Para cobrança por hora, informe o valor da hora trabalhada.')
                })
            if not horas_trabalhadas:
                raise ValidationError({
                    'horas_trabalhadas': _('Para cobrança por hora, informe quantas horas foram trabalhadas.')
                })
            if valor_hora <= 0:
                raise ValidationError({
                    'valor_hora': _('O valor da hora deve ser maior que zero.')
                })
            if horas_trabalhadas <= 0:
                raise ValidationError({
                    'horas_trabalhadas': _('As horas trabalhadas devem ser maior que zero.')
                })
        
        elif tipo_cobranca == 'por_exito':
            if not percentual_exito:
                raise ValidationError({
                    'percentual_exito': _('Para cobrança por êxito, informe o percentual sobre o resultado.')
                })
            if not valor_exito:
                raise ValidationError({
                    'valor_exito': _('Para cobrança por êxito, informe o valor base para cálculo.')
                })
            if percentual_exito <= 0 or percentual_exito > 100:
                raise ValidationError({
                    'percentual_exito': _('O percentual deve estar entre 0,01% e 100%.')
                })
            if valor_exito <= 0:
                raise ValidationError({
                    'valor_exito': _('O valor base deve ser maior que zero.')
                })
        
        elif tipo_cobranca == 'misto':
            if not valor_fixo and not (percentual_exito and valor_exito):
                raise ValidationError(
                    _('Para cobrança mista, informe pelo menos o valor fixo OU o percentual de êxito.')
                )
        
        # Validar se cliente e processo são compatíveis
        if processo and cliente and processo.cliente != cliente:
            raise ValidationError(
                _('O cliente selecionado deve ser o mesmo cliente do processo escolhido.')
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
            ).select_related('cliente')
        else:
            self.fields['processo'].queryset = Processo.objects.select_related(
                'cliente'
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