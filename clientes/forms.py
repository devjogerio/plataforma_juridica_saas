from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import date, timedelta
import re
from .models import Cliente, InteracaoCliente, ParteEnvolvida


class ClienteForm(forms.ModelForm):
    """Formulário para criação e edição de clientes"""
    
    class Meta:
        model = Cliente
        fields = [
            'tipo_pessoa', 'nome_razao_social', 'cpf_cnpj', 'rg_ie',
            'data_nascimento', 'profissao',
            'email', 'telefone', 'telefone_secundario', 'endereco',
            'cidade', 'estado', 'cep', 'observacoes', 'ativo'
        ]
        widgets = {
            'tipo_pessoa': forms.Select(attrs={'class': 'form-select'}),
            'nome_razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '000.000.000-00'}),
            'rg_ie': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profissao': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 0000-0000'}),
            'telefone_secundario': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '00000-000'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'tipo_pessoa': 'Tipo de Pessoa',
            'nome_razao_social': 'Nome/Razão Social',
            'cpf_cnpj': 'CPF/CNPJ',
            'rg_ie': 'RG/IE',
            'data_nascimento': 'Data de Nascimento',
            'profissao': 'Profissão',
            'email': 'E-mail',
            'telefone': 'Telefone',
            'telefone_secundario': 'Telefone Secundário',
            'endereco': 'Endereço',
            'cidade': 'Cidade',
            'estado': 'Estado',
            'cep': 'CEP',
            'observacoes': 'Observações',
            'ativo': 'Ativo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajustar campos baseado no tipo de pessoa
        if self.instance and self.instance.pk:
            if self.instance.tipo_pessoa == 'pf':
                self.fields['cpf_cnpj'].widget.attrs['data-mask'] = '000.000.000-00'
                self.fields['cpf_cnpj'].label = 'CPF'
                self.fields['rg_ie'].label = 'RG'
            else:
                self.fields['cpf_cnpj'].widget.attrs['data-mask'] = '00.000.000/0000-00'
                self.fields['cpf_cnpj'].label = 'CNPJ'
                self.fields['rg_ie'].label = 'IE'
                # Para PJ, data de nascimento não é obrigatória
                self.fields['data_nascimento'].required = False
    
    def clean_cpf_cnpj(self):
        """Validação de CPF/CNPJ"""
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj', '').replace('.', '').replace('-', '').replace('/', '')
        
        if not cpf_cnpj:
            return cpf_cnpj
            
        if len(cpf_cnpj) == 11:
            # Validação básica de CPF
            if not self._validar_cpf(cpf_cnpj):
                raise ValidationError('CPF inválido.')
        elif len(cpf_cnpj) == 14:
            # Validação básica de CNPJ
            if not self._validar_cnpj(cpf_cnpj):
                raise ValidationError('CNPJ inválido.')
        else:
            raise ValidationError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos.')
            
        return cpf_cnpj
    
    def _validar_cpf(self, cpf):
        """Validação básica de CPF"""
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Cálculo do primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Cálculo do segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return cpf[-2:] == f"{digito1}{digito2}"
    
    def _validar_cnpj(self, cnpj):
        """Validação básica de CNPJ"""
        if len(cnpj) != 14:
            return False
        
        # Cálculo do primeiro dígito verificador
        multiplicadores1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * multiplicadores1[i] for i in range(12))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Cálculo do segundo dígito verificador
        multiplicadores2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * multiplicadores2[i] for i in range(13))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return cnpj[-2:] == f"{digito1}{digito2}"
    
    def clean_email(self):
        """Validação de email"""
        email = self.cleaned_data.get('email')
        if email:
            # Verifica se já existe outro cliente com este email
            if self.instance.pk:
                if Cliente.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Já existe um cliente com este email.')
            else:
                if Cliente.objects.filter(email=email).exists():
                    raise ValidationError('Já existe um cliente com este email.')
        return email
    
    def clean_nome_razao_social(self):
        """Validação do nome/razão social"""
        nome = self.cleaned_data.get('nome_razao_social', '').strip()
        
        if not nome:
            raise ValidationError('Nome/Razão Social é obrigatório.')
        
        if len(nome) < 2:
            raise ValidationError('Nome/Razão Social deve ter pelo menos 2 caracteres.')
        
        if len(nome) > 255:
            raise ValidationError('Nome/Razão Social não pode exceder 255 caracteres.')
        
        # Verifica se contém apenas caracteres válidos
        if not re.match(r'^[a-zA-ZÀ-ÿ\s\.\-\']+$', nome):
            raise ValidationError('Nome/Razão Social contém caracteres inválidos.')
        
        return nome
    
    def clean_data_nascimento(self):
        """Validação da data de nascimento"""
        data_nascimento = self.cleaned_data.get('data_nascimento')
        tipo_pessoa = self.cleaned_data.get('tipo_pessoa')
        
        if data_nascimento:
            hoje = date.today()
            
            # Verifica se a data não é futura
            if data_nascimento > hoje:
                raise ValidationError('Data de nascimento não pode ser futura.')
            
            # Para pessoa física, verifica idade mínima e máxima
            if tipo_pessoa == 'PF':
                idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
                
                if idade < 16:
                    raise ValidationError('Cliente deve ter pelo menos 16 anos.')
                
                if idade > 120:
                    raise ValidationError('Data de nascimento inválida (idade superior a 120 anos).')
            
            # Para pessoa jurídica, verifica se não é muito antiga
            elif tipo_pessoa == 'PJ':
                if data_nascimento < date(1800, 1, 1):
                    raise ValidationError('Data de fundação muito antiga.')
        
        return data_nascimento
    
    def clean_telefone(self):
        """Validação do telefone"""
        telefone = self.cleaned_data.get('telefone')
        
        if telefone:
            telefone = telefone.strip()
            # Remove caracteres especiais para validação
            telefone_limpo = re.sub(r'[^\d]', '', telefone)
            
            if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
                raise ValidationError('Telefone deve ter 10 ou 11 dígitos.')
            
            # Verifica se não são todos os dígitos iguais
            if len(set(telefone_limpo)) == 1:
                raise ValidationError('Telefone inválido.')
        
        return telefone
    
    def clean_cep(self):
        """Validação do CEP"""
        cep = self.cleaned_data.get('cep')
        
        if cep:
            cep = cep.strip()
            # Remove caracteres especiais
            cep_limpo = re.sub(r'[^\d]', '', cep)
            
            if len(cep_limpo) != 8:
                raise ValidationError('CEP deve ter 8 dígitos.')
            
            # Verifica se não são todos os dígitos iguais
            if len(set(cep_limpo)) == 1:
                raise ValidationError('CEP inválido.')
        
        return cep
    
    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        tipo_pessoa = cleaned_data.get('tipo_pessoa')
        cpf_cnpj = cleaned_data.get('cpf_cnpj', '')
        
        # Validação cruzada entre tipo de pessoa e documento
        if tipo_pessoa and cpf_cnpj:
            cpf_cnpj_limpo = re.sub(r'[^\d]', '', cpf_cnpj)
            
            if tipo_pessoa == 'PF' and len(cpf_cnpj_limpo) != 11:
                raise ValidationError('Para Pessoa Física, informe um CPF válido (11 dígitos).')
            
            if tipo_pessoa == 'PJ' and len(cpf_cnpj_limpo) != 14:
                raise ValidationError('Para Pessoa Jurídica, informe um CNPJ válido (14 dígitos).')
        
        # Validação de endereço completo
        endereco = cleaned_data.get('endereco')
        cidade = cleaned_data.get('cidade')
        estado = cleaned_data.get('estado')
        cep = cleaned_data.get('cep')
        
        # Se um campo de endereço foi preenchido, outros campos relacionados devem ser preenchidos
        campos_endereco = [endereco, cidade, estado, cep]
        campos_preenchidos = [campo for campo in campos_endereco if campo]
        
        if campos_preenchidos and len(campos_preenchidos) < 3:
            raise ValidationError('Se informar endereço, preencha pelo menos cidade, estado e CEP.')
        
        return cleaned_data


class InteracaoClienteForm(forms.ModelForm):
    """Formulário para registro de interações com clientes"""
    
    class Meta:
        model = InteracaoCliente
        fields = ['tipo_interacao', 'assunto', 'descricao', 'data_interacao', 'processo_relacionado']
        widgets = {
            'tipo_interacao': forms.Select(attrs={'class': 'form-select'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'data_interacao': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'processo_relacionado': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'tipo_interacao': 'Tipo de Interação',
            'assunto': 'Assunto',
            'descricao': 'Descrição',
            'data_interacao': 'Data da Interação',
            'processo_relacionado': 'Processo Relacionado',
        }


class ParteEnvolvidaForm(forms.ModelForm):
    """Formulário para partes envolvidas"""
    
    class Meta:
        model = ParteEnvolvida
        fields = [
            'nome', 'tipo_envolvimento', 'cpf_cnpj', 'oab_numero', 'oab_uf',
            'email', 'telefone', 'endereco', 'observacoes'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_envolvimento': forms.Select(attrs={'class': 'form-select'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'oab_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'oab_uf': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nome': 'Nome',
            'tipo_envolvimento': 'Tipo de Envolvimento',
            'cpf_cnpj': 'CPF/CNPJ',
            'oab_numero': 'Número OAB',
            'oab_uf': 'UF OAB',
            'email': 'E-mail',
            'telefone': 'Telefone',
            'endereco': 'Endereço',
            'observacoes': 'Observações',
        }


class ClienteFilterForm(forms.Form):
    """Formulário para filtros de clientes"""
    
    nome = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome ou Razão Social'
        })
    )
    
    tipo_pessoa = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Cliente.TIPO_PESSOA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Cliente.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    ativo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('true', 'Ativos'), ('false', 'Inativos')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )