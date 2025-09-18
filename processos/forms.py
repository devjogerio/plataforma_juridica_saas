from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import Processo
from clientes.models import Cliente
from usuarios.models import Usuario
import json


class ProcessoForm(forms.ModelForm):
    """
    Formulário para criação e edição de processos jurídicos.
    Inclui validações específicas e campos obrigatórios.
    """
    
    # Campo adicional para área do direito que controlará os tipos disponíveis
    area_direito_temp = forms.ChoiceField(
        choices=Processo.AREA_DIREITO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_area_direito_temp'
        }),
        label=_('Área do Direito'),
        required=True
    )
    
    # Campo adicional para estado que controlará as comarcas disponíveis
    estado_temp = forms.ChoiceField(
        choices=[
            ('ac', _('Acre')),
            ('al', _('Alagoas')),
            ('ap', _('Amapá')),
            ('am', _('Amazonas')),
            ('ba', _('Bahia')),
            ('ce', _('Ceará')),
            ('df', _('Distrito Federal')),
            ('es', _('Espírito Santo')),
            ('go', _('Goiás')),
            ('ma', _('Maranhão')),
            ('mt', _('Mato Grosso')),
            ('ms', _('Mato Grosso do Sul')),
            ('mg', _('Minas Gerais')),
            ('pa', _('Pará')),
            ('pb', _('Paraíba')),
            ('pr', _('Paraná')),
            ('pe', _('Pernambuco')),
            ('pi', _('Piauí')),
            ('rj', _('Rio de Janeiro')),
            ('rn', _('Rio Grande do Norte')),
            ('rs', _('Rio Grande do Sul')),
            ('ro', _('Rondônia')),
            ('rr', _('Roraima')),
            ('sc', _('Santa Catarina')),
            ('sp', _('São Paulo')),
            ('se', _('Sergipe')),
            ('to', _('Tocantins')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_estado_temp'
        }),
        label=_('Estado'),
        required=True
    )

    class Meta:
        model = Processo
        fields = [
            'numero_processo', 'area_direito_temp', 'tipo_processo', 'instancia',
            'valor_causa', 'estado_temp', 'comarca_tribunal', 'vara_orgao', 'juiz',
            'data_inicio', 'assunto', 'observacoes', 'cliente', 'usuario_responsavel'
        ]
        
        widgets = {
            'numero_processo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 1234567-89.2024.8.26.0001',
                'maxlength': 50
            }),
            'tipo_processo': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_tipo_processo'
            }),
            'instancia': forms.Select(attrs={
                'class': 'form-select'
            }),
            'valor_causa': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00'
            }),
            'comarca_tribunal': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_comarca_tribunal'
            }),
            'vara_orgao': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_vara_orgao'
            }),
            'juiz': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do juiz responsável',
                'maxlength': 200
            }),
            'data_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'assunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Resumo do objeto do processo',
                'maxlength': 500
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Informações adicionais sobre o processo...'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Selecione o cliente...'
            }),
            'usuario_responsavel': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Selecione o advogado responsável...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa o formulário com configurações específicas.
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configura queryset para clientes ativos
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True).order_by('nome_razao_social')
        
        # Configura queryset para usuários ativos
        self.fields['usuario_responsavel'].queryset = Usuario.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Se há um usuário logado, define como responsável padrão
        if user and not self.instance.pk:
            self.fields['usuario_responsavel'].initial = user
            
        # Configura o campo tipo_processo inicialmente vazio
        self.fields['tipo_processo'].choices = [('', 'Selecione primeiro a área do direito')]
        
        # Configura os campos comarca_tribunal e vara_orgao inicialmente vazios
        self.fields['comarca_tribunal'].choices = [('', 'Selecione primeiro o estado')]
        self.fields['vara_orgao'].choices = [('', 'Selecione primeiro a comarca/tribunal')]
        
        # Se estamos editando um processo existente, configura os valores
        if self.instance.pk and self.instance.area_direito:
            self.fields['area_direito_temp'].initial = self.instance.area_direito
            # Configura as opções de tipo_processo baseado na área
            area_data = Processo.TIPOS_PROCESSO_POR_AREA.get(self.instance.area_direito, {})
            if area_data:
                self.fields['tipo_processo'].choices = [('', 'Selecione o tipo de processo')] + area_data.get('tipos', [])
    
    def get_tipos_processo_json(self):
        """
        Retorna os tipos de processo organizados por área em formato JSON para JavaScript.
        """
        # Converte objetos de tradução para strings para evitar erro de serialização
        tipos_serializaveis = {}
        for area_key, area_data in Processo.TIPOS_PROCESSO_POR_AREA.items():
            tipos_serializaveis[area_key] = []
            for tipo_value, tipo_label in area_data.get('tipos', []):
                tipos_serializaveis[area_key].append({
                    'value': str(tipo_value),
                    'label': str(tipo_label)
                })
        return json.dumps(tipos_serializaveis)
    
    def get_comarcas_tribunais_json(self):
        """
        Retorna as comarcas/tribunais organizadas por estado em formato JSON para JavaScript.
        """
        # Converte objetos de tradução para strings para evitar erro de serialização
        comarcas_serializaveis = {}
        for estado_key, estado_data in Processo.COMARCAS_TRIBUNAIS_POR_ESTADO.items():
            comarcas_serializaveis[estado_key] = []
            for comarca_value, comarca_label in estado_data.get('comarcas', []):
                comarcas_serializaveis[estado_key].append({
                    'value': str(comarca_value),
                    'label': str(comarca_label)
                })
        return json.dumps(comarcas_serializaveis)
    
    def get_varas_orgaos_json(self):
        """
        Retorna as varas/órgãos organizadas por comarca/tribunal em formato JSON para JavaScript.
        """
        # Converte objetos de tradução para strings para evitar erro de serialização
        varas_serializaveis = {}
        for comarca_key, comarca_data in Processo.VARAS_ORGAOS_POR_COMARCA.items():
            varas_serializaveis[comarca_key] = []
            for vara_value, vara_label in comarca_data.get('varas', []):
                varas_serializaveis[comarca_key].append({
                    'value': str(vara_value),
                    'label': str(vara_label)
                })
        return json.dumps(varas_serializaveis)
    
    def clean(self):
        """
        Validação customizada do formulário.
        """
        cleaned_data = super().clean()
        area_direito = cleaned_data.get('area_direito_temp')
        tipo_processo = cleaned_data.get('tipo_processo')
        
        if area_direito and tipo_processo:
            # Verifica se o tipo de processo é válido para a área selecionada
            area_data = Processo.TIPOS_PROCESSO_POR_AREA.get(area_direito, {})
            tipos_validos = [tipo[0] for tipo in area_data.get('tipos', [])]
            
            if tipo_processo not in tipos_validos:
                raise ValidationError({
                    'tipo_processo': _('Tipo de processo inválido para a área do direito selecionada.')
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Salva o processo, definindo a área do direito baseada no campo temporário.
        """
        instance = super().save(commit=False)
        
        # Define a área do direito baseada no campo temporário
        if self.cleaned_data.get('area_direito_temp'):
            instance.area_direito = self.cleaned_data['area_direito_temp']
        
        if commit:
            instance.save()
        
        return instance
        
        # Se há um cliente pré-selecionado via GET parameter
        if 'initial' in kwargs and 'cliente' in kwargs['initial']:
            cliente_id = kwargs['initial']['cliente']
            try:
                cliente = Cliente.objects.get(pk=cliente_id)
                self.fields['cliente'].initial = cliente
            except Cliente.DoesNotExist:
                pass
    
    def clean_numero_processo(self):
        """
        Valida o número do processo.
        """
        numero_processo = self.cleaned_data.get('numero_processo')
        
        if not numero_processo:
            raise ValidationError(_('O número do processo é obrigatório.'))
        
        # Remove espaços e caracteres especiais para validação
        numero_limpo = ''.join(filter(str.isalnum, numero_processo))
        
        if len(numero_limpo) < 10:
            raise ValidationError(
                _('O número do processo deve ter pelo menos 10 caracteres alfanuméricos.')
            )
        
        # Verifica se já existe outro processo com o mesmo número
        if self.instance.pk:
            existing = Processo.objects.filter(
                numero_processo=numero_processo
            ).exclude(pk=self.instance.pk)
        else:
            existing = Processo.objects.filter(numero_processo=numero_processo)
        
        if existing.exists():
            raise ValidationError(
                _('Já existe um processo cadastrado com este número.')
            )
        
        return numero_processo
    
    def clean_valor_causa(self):
        """
        Valida o valor da causa.
        """
        valor_causa = self.cleaned_data.get('valor_causa')
        
        if valor_causa is not None and valor_causa <= 0:
            raise ValidationError(
                _('O valor da causa deve ser maior que zero.')
            )
        
        return valor_causa
    
    def clean_data_inicio(self):
        """
        Valida a data de início do processo.
        """
        data_inicio = self.cleaned_data.get('data_inicio')
        
        if not data_inicio:
            raise ValidationError(_('A data de início é obrigatória.'))
        
        from datetime import date
        if data_inicio > date.today():
            raise ValidationError(
                _('A data de início não pode ser posterior à data atual.')
            )
        
        return data_inicio
    
    def clean_assunto(self):
        """
        Valida o assunto do processo.
        """
        assunto = self.cleaned_data.get('assunto')
        
        if not assunto or len(assunto.strip()) < 10:
            raise ValidationError(
                _('O assunto deve ter pelo menos 10 caracteres.')
            )
        
        return assunto.strip()
    
    def clean_tipo_processo(self):
        """
        Valida o campo tipo_processo baseado na área do direito selecionada.
        """
        tipo_processo = self.cleaned_data.get('tipo_processo')
        area_direito = self.cleaned_data.get('area_direito_temp')
        
        if not tipo_processo:
            raise ValidationError(_('Este campo é obrigatório.'))
        
        # Verifica se o tipo de processo é válido para a área selecionada
        if area_direito:
            area_data = Processo.TIPOS_PROCESSO_POR_AREA.get(area_direito, {})
            tipos_validos = [tipo[0] for tipo in area_data.get('tipos', [])]
            
            if tipo_processo not in tipos_validos:
                raise ValidationError(_('Tipo de processo inválido para a área selecionada.'))
        
        return tipo_processo

    def clean(self):
        """
        Validações gerais do formulário.
        """
        cleaned_data = super().clean()
        tipo_processo = cleaned_data.get('tipo_processo')
        valor_causa = cleaned_data.get('valor_causa')
        
        # Para processos judiciais, o valor da causa é obrigatório
        if tipo_processo == 'judicial' and not valor_causa:
            raise ValidationError({
                'valor_causa': _('O valor da causa é obrigatório para processos judiciais.')
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Salva o processo com configurações adicionais.
        """
        processo = super().save(commit=False)
        
        # Define a área do direito baseada no campo temporário
        area_direito_temp = self.cleaned_data.get('area_direito_temp')
        if area_direito_temp:
            processo.area_direito = area_direito_temp
        
        if commit:
            processo.save()
            
            # Se é um novo processo, cria andamento inicial
            if not self.instance.pk:
                from .models import Andamento
                Andamento.objects.create(
                    processo=processo,
                    data_andamento=processo.data_inicio,
                    tipo_andamento='outro',
                    descricao='Processo cadastrado no sistema',
                    usuario=processo.usuario_responsavel
                )
        
        return processo


class ProcessoPrimeiroForm(ProcessoForm):
    """
    Formulário específico para criação do primeiro processo.
    Inclui campos adicionais e validações específicas para novos usuários.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adiciona classes CSS específicas para o primeiro processo
        for field_name, field in self.fields.items():
            if 'class' in field.widget.attrs:
                field.widget.attrs['class'] += ' primeiro-processo'
            else:
                field.widget.attrs['class'] = 'primeiro-processo'
        
        # Torna alguns campos obrigatórios para o primeiro processo
        self.fields['comarca_tribunal'].required = True
        self.fields['assunto'].required = True
        
        # Adiciona help texts específicos
        self.fields['numero_processo'].help_text = _(
            'Digite o número completo do processo conforme consta no tribunal.'
        )
        self.fields['tipo_processo'].help_text = _(
            'Selecione o tipo que melhor descreve seu processo.'
        )
        self.fields['area_direito'].help_text = _(
            'Escolha a área do direito relacionada ao processo.'
        )
    
    def clean(self):
        """
        Validações específicas para o primeiro processo.
        """
        cleaned_data = super().clean()
        
        # Validações adicionais para garantir qualidade dos dados
        comarca_tribunal = cleaned_data.get('comarca_tribunal')
        if comarca_tribunal and len(comarca_tribunal.strip()) < 5:
            raise ValidationError({
                'comarca_tribunal': _('O nome da comarca/tribunal deve ter pelo menos 5 caracteres.')
            })
        
        return cleaned_data