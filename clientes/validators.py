"""
Validadores customizados para documentos brasileiros.

Este módulo contém validadores para CPF e CNPJ com verificação
completa dos dígitos verificadores.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validar_cpf(cpf):
    """
    Valida um CPF brasileiro com verificação completa dos dígitos verificadores.
    
    Args:
        cpf (str): CPF a ser validado (pode conter formatação)
        
    Raises:
        ValidationError: Se o CPF for inválido
        
    Returns:
        str: CPF limpo (apenas números) se válido
    """
    if not cpf:
        raise ValidationError(_('CPF é obrigatório'))
    
    # Remove formatação (pontos, hífens, espaços)
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    # Verifica se tem exatamente 11 dígitos
    if len(cpf_limpo) != 11:
        raise ValidationError(_('CPF deve conter exatamente 11 dígitos'))
    
    # Verifica se todos os dígitos são iguais (CPFs inválidos conhecidos)
    if cpf_limpo == cpf_limpo[0] * 11:
        raise ValidationError(_('CPF inválido: todos os dígitos são iguais'))
    
    # Calcula o primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf_limpo[i]) * (10 - i)
    
    primeiro_digito = 11 - (soma % 11)
    if primeiro_digito >= 10:
        primeiro_digito = 0
    
    # Verifica o primeiro dígito
    if int(cpf_limpo[9]) != primeiro_digito:
        raise ValidationError(_('CPF inválido: primeiro dígito verificador incorreto'))
    
    # Calcula o segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf_limpo[i]) * (11 - i)
    
    segundo_digito = 11 - (soma % 11)
    if segundo_digito >= 10:
        segundo_digito = 0
    
    # Verifica o segundo dígito
    if int(cpf_limpo[10]) != segundo_digito:
        raise ValidationError(_('CPF inválido: segundo dígito verificador incorreto'))
    
    return cpf_limpo


def validar_cnpj(cnpj):
    """
    Valida um CNPJ brasileiro com verificação completa dos dígitos verificadores.
    
    Args:
        cnpj (str): CNPJ a ser validado (pode conter formatação)
        
    Raises:
        ValidationError: Se o CNPJ for inválido
        
    Returns:
        str: CNPJ limpo (apenas números) se válido
    """
    if not cnpj:
        raise ValidationError(_('CNPJ é obrigatório'))
    
    # Remove formatação (pontos, barras, hífens, espaços)
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
    
    # Verifica se tem exatamente 14 dígitos
    if len(cnpj_limpo) != 14:
        raise ValidationError(_('CNPJ deve conter exatamente 14 dígitos'))
    
    # Verifica se todos os dígitos são iguais (CNPJs inválidos conhecidos)
    if cnpj_limpo == cnpj_limpo[0] * 14:
        raise ValidationError(_('CNPJ inválido: todos os dígitos são iguais'))
    
    # Sequência de pesos para o primeiro dígito verificador
    pesos_primeiro = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Calcula o primeiro dígito verificador
    soma = 0
    for i in range(12):
        soma += int(cnpj_limpo[i]) * pesos_primeiro[i]
    
    primeiro_digito = soma % 11
    if primeiro_digito < 2:
        primeiro_digito = 0
    else:
        primeiro_digito = 11 - primeiro_digito
    
    # Verifica o primeiro dígito
    if int(cnpj_limpo[12]) != primeiro_digito:
        raise ValidationError(_('CNPJ inválido: primeiro dígito verificador incorreto'))
    
    # Sequência de pesos para o segundo dígito verificador
    pesos_segundo = [6, 7, 8, 9, 2, 3, 4, 5, 6, 7, 8, 9, 2]
    
    # Calcula o segundo dígito verificador
    soma = 0
    for i in range(13):
        soma += int(cnpj_limpo[i]) * pesos_segundo[i]
    
    segundo_digito = soma % 11
    if segundo_digito < 2:
        segundo_digito = 0
    else:
        segundo_digito = 11 - segundo_digito
    
    # Verifica o segundo dígito
    if int(cnpj_limpo[13]) != segundo_digito:
        raise ValidationError(_('CNPJ inválido: segundo dígito verificador incorreto'))
    
    return cnpj_limpo


def formatar_cpf(cpf):
    """
    Formata um CPF no padrão brasileiro (000.000.000-00).
    
    Args:
        cpf (str): CPF limpo (apenas números)
        
    Returns:
        str: CPF formatado
    """
    if len(cpf) != 11:
        return cpf
    
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def formatar_cnpj(cnpj):
    """
    Formata um CNPJ no padrão brasileiro (00.000.000/0000-00).
    
    Args:
        cnpj (str): CNPJ limpo (apenas números)
        
    Returns:
        str: CNPJ formatado
    """
    if len(cnpj) != 14:
        return cnpj
    
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def limpar_documento(documento):
    """
    Remove formatação de um documento (CPF ou CNPJ).
    
    Args:
        documento (str): Documento com ou sem formatação
        
    Returns:
        str: Documento limpo (apenas números)
    """
    if not documento:
        return ''
    
    return ''.join(filter(str.isdigit, documento))