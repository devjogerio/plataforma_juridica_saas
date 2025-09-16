from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta
import json

from .models import TemplateRelatorio, DashboardPersonalizado, FiltroSalvo
from processos.models import Processo
from clientes.models import Cliente
from usuarios.models import Usuario


class TemplateRelatorioForm(forms.ModelForm):
    """
    Formulário para criação e edição de templates de relatórios
    """
    
    class Meta:
        model = TemplateRelatorio
        fields = [
            'nome', 'descricao', 'tipo_relatorio', 'formato_saida',
            'campos_selecionados', 'filtros_padrao', 'ordenacao_padrao',
            'agrupamento', 'configuracoes_layout', 'publico'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do template de relatório...'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do que o relatório apresenta...'
            }),
            'tipo_relatorio': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'atualizarCamposDisponiveis()'
            }),
            'formato_saida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'publico': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    # Campos dinâmicos para seleção de campos do relatório
    campos_processos = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Campos de Processos'
    )
    
    campos_clientes = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Campos de Clientes'
    )
    
    campos_financeiro = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Campos Financeiros'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Definir choices para campos disponíveis
        self._definir_campos_disponiveis()
        
        # Se editando, carregar campos selecionados
        if self.instance.pk:
            self._carregar_campos_selecionados()
    
    def _definir_campos_disponiveis(self):
        """
        Define os campos disponíveis para cada tipo de relatório
        """
        # Campos de processos
        self.fields['campos_processos'].choices = [
            ('numero_processo', 'Número do Processo'),
            ('tipo_processo', 'Tipo de Processo'),
            ('area_direito', 'Área do Direito'),
            ('status', 'Status'),
            ('data_inicio', 'Data de Início'),
            ('data_encerramento', 'Data de Encerramento'),
            ('valor_causa', 'Valor da Causa'),
            ('comarca', 'Comarca'),
            ('vara', 'Vara'),
            ('responsavel', 'Responsável'),
            ('observacoes', 'Observações'),
        ]
        
        # Campos de clientes
        self.fields['campos_clientes'].choices = [
            ('nome_razao_social', 'Nome/Razão Social'),
            ('nome_fantasia', 'Nome Fantasia'),
            ('tipo_pessoa', 'Tipo de Pessoa'),
            ('cpf_cnpj', 'CPF/CNPJ'),
            ('email', 'E-mail'),
            ('telefone', 'Telefone'),
            ('cidade', 'Cidade'),
            ('uf', 'UF'),
            ('data_cadastro', 'Data de Cadastro'),
        ]
        
        # Campos financeiros
        self.fields['campos_financeiro'].choices = [
            ('valor_honorarios', 'Valor dos Honorários'),
            ('status_pagamento', 'Status do Pagamento'),
            ('data_vencimento', 'Data de Vencimento'),
            ('data_pagamento', 'Data de Pagamento'),
            ('valor_despesas', 'Valor das Despesas'),
            ('tipo_cobranca', 'Tipo de Cobrança'),
        ]
    
    def _carregar_campos_selecionados(self):
        """
        Carrega os campos já selecionados no template
        """
        campos_selecionados = self.instance.campos_selecionados or []
        
        # Separar campos por categoria
        campos_processos = []
        campos_clientes = []
        campos_financeiro = []
        
        for campo in campos_selecionados:
            if campo.startswith('processo_'):
                campos_processos.append(campo.replace('processo_', ''))
            elif campo.startswith('cliente_'):
                campos_clientes.append(campo.replace('cliente_', ''))
            elif campo.startswith('financeiro_'):
                campos_financeiro.append(campo.replace('financeiro_', ''))
        
        self.fields['campos_processos'].initial = campos_processos
        self.fields['campos_clientes'].initial = campos_clientes
        self.fields['campos_financeiro'].initial = campos_financeiro
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_relatorio = cleaned_data.get('tipo_relatorio')
        campos_processos = cleaned_data.get('campos_processos', [])
        campos_clientes = cleaned_data.get('campos_clientes', [])
        campos_financeiro = cleaned_data.get('campos_financeiro', [])
        
        # Validar se pelo menos um campo foi selecionado
        total_campos = len(campos_processos) + len(campos_clientes) + len(campos_financeiro)
        if total_campos == 0:
            raise ValidationError(
                _('Selecione pelo menos um campo para incluir no relatório.')
            )
        
        # Montar lista de campos selecionados
        campos_selecionados = []
        campos_selecionados.extend([f'processo_{campo}' for campo in campos_processos])
        campos_selecionados.extend([f'cliente_{campo}' for campo in campos_clientes])
        campos_selecionados.extend([f'financeiro_{campo}' for campo in campos_financeiro])
        
        cleaned_data['campos_selecionados'] = campos_selecionados
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Definir usuário criador se não estiver definido
        if not instance.usuario_criador_id and hasattr(self, 'user'):
            instance.usuario_criador = self.user
        
        if commit:
            instance.save()
        
        return instance


class FiltroRelatorioForm(forms.Form):
    """
    Formulário para aplicar filtros em relatórios
    """
    
    PERIODO_CHOICES = [
        ('', 'Selecione o período...'),
        ('hoje', 'Hoje'),
        ('ontem', 'Ontem'),
        ('esta_semana', 'Esta Semana'),
        ('semana_passada', 'Semana Passada'),
        ('este_mes', 'Este Mês'),
        ('mes_passado', 'Mês Passado'),
        ('ultimo_trimestre', 'Último Trimestre'),
        ('este_ano', 'Este Ano'),
        ('ano_passado', 'Ano Passado'),
        ('personalizado', 'Período Personalizado'),
    ]
    
    # Filtros gerais
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
    
    # Filtros específicos de processos
    tipo_processo = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + Processo.TIPO_PROCESSO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    area_direito = forms.ChoiceField(
        choices=[('', 'Todas as áreas')] + Processo.AREA_DIREITO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status_processo = forms.ChoiceField(
        choices=[('', 'Todos os status')] + Processo.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    responsavel = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(is_active=True),
        required=False,
        empty_label='Todos os responsáveis',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Filtros específicos de clientes
    tipo_pessoa = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + Cliente.TIPO_PESSOA_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    uf_cliente = forms.ChoiceField(
        choices=[('', 'Todos os estados')] + [
            ('SP', 'São Paulo'), ('RJ', 'Rio de Janeiro'), ('MG', 'Minas Gerais'),
            ('RS', 'Rio Grande do Sul'), ('PR', 'Paraná'), ('SC', 'Santa Catarina'),
            ('BA', 'Bahia'), ('GO', 'Goiás'), ('PE', 'Pernambuco'), ('CE', 'Ceará')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Filtros financeiros
    valor_causa_min = forms.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=15,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0,00'
        })
    )
    
    valor_causa_max = forms.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=15,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0,00'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        tipo_relatorio = kwargs.pop('tipo_relatorio', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar responsáveis por usuário se não for staff
        if user and not user.is_staff:
            self.fields['responsavel'].queryset = Usuario.objects.filter(
                id=user.id
            )
        
        # Mostrar/ocultar campos baseado no tipo de relatório
        if tipo_relatorio:
            self._configurar_campos_por_tipo(tipo_relatorio)
    
    def _configurar_campos_por_tipo(self, tipo_relatorio):
        """
        Configura quais campos mostrar baseado no tipo de relatório
        """
        if tipo_relatorio == 'clientes':
            # Ocultar campos específicos de processos
            del self.fields['tipo_processo']
            del self.fields['area_direito']
            del self.fields['status_processo']
            del self.fields['valor_causa_min']
            del self.fields['valor_causa_max']
        
        elif tipo_relatorio == 'financeiro':
            # Manter todos os campos financeiros
            pass
        
        elif tipo_relatorio == 'processos':
            # Ocultar campos específicos de clientes
            del self.fields['tipo_pessoa']
    
    def clean(self):
        cleaned_data = super().clean()
        periodo = cleaned_data.get('periodo')
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        valor_causa_min = cleaned_data.get('valor_causa_min')
        valor_causa_max = cleaned_data.get('valor_causa_max')
        
        # Validar período personalizado
        if periodo == 'personalizado':
            if not data_inicio or not data_fim:
                raise ValidationError(
                    _('Para período personalizado, informe data de início e fim.')
                )
            
            if data_inicio > data_fim:
                raise ValidationError(
                    _('Data de início deve ser anterior à data de fim.')
                )
        
        # Validar valores de causa
        if valor_causa_min and valor_causa_max:
            if valor_causa_min > valor_causa_max:
                raise ValidationError(
                    _('Valor mínimo deve ser menor que o valor máximo.')
                )
        
        return cleaned_data


class DashboardPersonalizadoForm(forms.ModelForm):
    """
    Formulário para criação e edição de dashboards personalizados
    """
    
    class Meta:
        model = DashboardPersonalizado
        fields = ['nome', 'descricao', 'publico', 'padrao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do dashboard...'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do dashboard...'
            }),
            'publico': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'padrao': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Se marcado como padrão, desmarcar outros dashboards padrão do usuário
        if instance.padrao and instance.usuario_id:
            DashboardPersonalizado.objects.filter(
                usuario=instance.usuario,
                padrao=True
            ).exclude(id=instance.id).update(padrao=False)
        
        if commit:
            instance.save()
        
        return instance


class FiltroSalvoForm(forms.ModelForm):
    """
    Formulário para salvar filtros personalizados
    """
    
    class Meta:
        model = FiltroSalvo
        fields = ['nome', 'descricao', 'tipo_filtro', 'publico', 'favorito']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do filtro...'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descrição do filtro...'
            }),
            'tipo_filtro': forms.Select(attrs={
                'class': 'form-select'
            }),
            'publico': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'favorito': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class ExportarRelatorioForm(forms.Form):
    """
    Formulário para configurações de exportação de relatórios
    """
    
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    ORIENTACAO_CHOICES = [
        ('portrait', 'Retrato'),
        ('landscape', 'Paisagem'),
    ]
    
    formato = forms.ChoiceField(
        choices=FORMATO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    orientacao = forms.ChoiceField(
        choices=ORIENTACAO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    incluir_graficos = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    incluir_cabecalho = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    incluir_rodape = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    titulo_personalizado = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Título personalizado do relatório...'
        })
    )
    
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações adicionais...'
        })
    )