"""
Testes para os validadores de CPF e CNPJ.

Este módulo testa todas as funcionalidades dos validadores customizados
incluindo casos válidos, inválidos e edge cases.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from clientes.validators import (
    validar_cpf, validar_cnpj, formatar_cpf, formatar_cnpj, limpar_documento
)


class TestValidadorCPF(TestCase):
    """Testes para o validador de CPF."""
    
    def test_cpf_valido_sem_formatacao(self):
        """Testa CPF válido sem formatação."""
        cpf_valido = "11144477735"  # CPF válido conhecido
        resultado = validar_cpf(cpf_valido)
        self.assertEqual(resultado, cpf_valido)
    
    def test_cpf_valido_com_formatacao(self):
        """Testa CPF válido com formatação."""
        cpf_formatado = "111.444.777-35"
        cpf_esperado = "11144477735"
        resultado = validar_cpf(cpf_formatado)
        self.assertEqual(resultado, cpf_esperado)
    
    def test_cpf_vazio(self):
        """Testa CPF vazio."""
        with self.assertRaises(ValidationError) as context:
            validar_cpf("")
        self.assertIn("CPF é obrigatório", str(context.exception))
    
    def test_cpf_none(self):
        """Testa CPF None."""
        with self.assertRaises(ValidationError) as context:
            validar_cpf(None)
        self.assertIn("CPF é obrigatório", str(context.exception))
    
    def test_cpf_tamanho_incorreto(self):
        """Testa CPF com tamanho incorreto."""
        with self.assertRaises(ValidationError) as context:
            validar_cpf("123456789")  # 9 dígitos
        self.assertIn("deve conter exatamente 11 dígitos", str(context.exception))
        
        with self.assertRaises(ValidationError) as context:
            validar_cpf("123456789012")  # 12 dígitos
        self.assertIn("deve conter exatamente 11 dígitos", str(context.exception))
    
    def test_cpf_todos_digitos_iguais(self):
        """Testa CPF com todos os dígitos iguais."""
        cpfs_invalidos = [
            "00000000000", "11111111111", "22222222222",
            "33333333333", "44444444444", "55555555555",
            "66666666666", "77777777777", "88888888888",
            "99999999999"
        ]
        
        for cpf in cpfs_invalidos:
            with self.assertRaises(ValidationError) as context:
                validar_cpf(cpf)
            self.assertIn("todos os dígitos são iguais", str(context.exception))
    
    def test_cpf_primeiro_digito_incorreto(self):
        """Testa CPF com primeiro dígito verificador incorreto."""
        with self.assertRaises(ValidationError) as context:
            validar_cpf("11144477745")  # Último dígito alterado
        self.assertIn("primeiro dígito verificador incorreto", str(context.exception))
    
    def test_cpf_segundo_digito_incorreto(self):
        """Testa CPF com segundo dígito verificador incorreto."""
        with self.assertRaises(ValidationError) as context:
            validar_cpf("11144477734")  # Último dígito alterado
        self.assertIn("segundo dígito verificador incorreto", str(context.exception))


class TestValidadorCNPJ(TestCase):
    """Testes para o validador de CNPJ."""
    
    def test_cnpj_valido_sem_formatacao(self):
        """Testa CNPJ válido sem formatação."""
        cnpj_valido = "11222333000189"  # CNPJ válido calculado: 11.222.333/0001-89
        resultado = validar_cnpj(cnpj_valido)
        self.assertEqual(resultado, cnpj_valido)
    
    def test_cnpj_valido_com_formatacao(self):
        """Testa CNPJ válido com formatação."""
        cnpj_formatado = "11.222.333/0001-89"
        cnpj_esperado = "11222333000189"
        resultado = validar_cnpj(cnpj_formatado)
        self.assertEqual(resultado, cnpj_esperado)
    
    def test_cnpj_vazio(self):
        """Testa CNPJ vazio."""
        with self.assertRaises(ValidationError) as context:
            validar_cnpj("")
        self.assertIn("CNPJ é obrigatório", str(context.exception))
    
    def test_cnpj_none(self):
        """Testa CNPJ None."""
        with self.assertRaises(ValidationError) as context:
            validar_cnpj(None)
        self.assertIn("CNPJ é obrigatório", str(context.exception))
    
    def test_cnpj_tamanho_incorreto(self):
        """Testa CNPJ com tamanho incorreto."""
        with self.assertRaises(ValidationError) as context:
            validar_cnpj("1234567890123")  # 13 dígitos
        self.assertIn("deve conter exatamente 14 dígitos", str(context.exception))
        
        with self.assertRaises(ValidationError) as context:
            validar_cnpj("123456789012345")  # 15 dígitos
        self.assertIn("deve conter exatamente 14 dígitos", str(context.exception))
    
    def test_cnpj_todos_digitos_iguais(self):
        """Testa CNPJ com todos os dígitos iguais."""
        cnpjs_invalidos = [
            "00000000000000", "11111111111111", "22222222222222",
            "33333333333333", "44444444444444", "55555555555555",
            "66666666666666", "77777777777777", "88888888888888",
            "99999999999999"
        ]
        
        for cnpj in cnpjs_invalidos:
            with self.assertRaises(ValidationError) as context:
                validar_cnpj(cnpj)
            self.assertIn("todos os dígitos são iguais", str(context.exception))
    
    def test_cnpj_primeiro_digito_incorreto(self):
        """Testa CNPJ com primeiro dígito verificador incorreto."""
        with self.assertRaises(ValidationError) as context:
            validar_cnpj("11222333000199")  # Penúltimo dígito alterado (8->9)
        self.assertIn("primeiro dígito verificador incorreto", str(context.exception))
    
    def test_cnpj_segundo_digito_incorreto(self):
        """Testa CNPJ com segundo dígito verificador incorreto."""
        with self.assertRaises(ValidationError) as context:
            validar_cnpj("11222333000188")  # Último dígito alterado (9->8)
        self.assertIn("segundo dígito verificador incorreto", str(context.exception))


class TestFormatadores(TestCase):
    """Testes para os formatadores de documentos."""
    
    def test_formatar_cpf(self):
        """Testa formatação de CPF."""
        cpf_limpo = "11144477735"
        cpf_formatado = formatar_cpf(cpf_limpo)
        self.assertEqual(cpf_formatado, "111.444.777-35")
    
    def test_formatar_cpf_tamanho_incorreto(self):
        """Testa formatação de CPF com tamanho incorreto."""
        cpf_incorreto = "123456789"
        resultado = formatar_cpf(cpf_incorreto)
        self.assertEqual(resultado, cpf_incorreto)  # Retorna sem formatação
    
    def test_formatar_cnpj(self):
        """Testa formatação de CNPJ."""
        cnpj_limpo = "11222333000189"
        cnpj_formatado = formatar_cnpj(cnpj_limpo)
        self.assertEqual(cnpj_formatado, "11.222.333/0001-89")
    
    def test_formatar_cnpj_tamanho_incorreto(self):
        """Testa formatação de CNPJ com tamanho incorreto."""
        cnpj_incorreto = "123456789012"
        resultado = formatar_cnpj(cnpj_incorreto)
        self.assertEqual(resultado, cnpj_incorreto)  # Retorna sem formatação
    
    def test_limpar_documento(self):
        """Testa limpeza de documento."""
        casos_teste = [
            ("111.444.777-35", "11144477735"),
            ("11.222.333/0001-89", "11222333000189"),
            ("111 444 777 35", "11144477735"),
            ("11144477735", "11144477735"),
            ("", ""),
            (None, ""),
        ]
        
        for documento_formatado, documento_limpo in casos_teste:
            resultado = limpar_documento(documento_formatado)
            self.assertEqual(resultado, documento_limpo)


class TestIntegracao(TestCase):
    """Testes de integração dos validadores."""
    
    def test_fluxo_completo_cpf(self):
        """Testa fluxo completo de validação e formatação de CPF."""
        cpf_entrada = "111.444.777-35"
        
        # Valida e obtém CPF limpo
        cpf_limpo = validar_cpf(cpf_entrada)
        self.assertEqual(cpf_limpo, "11144477735")
        
        # Formata novamente
        cpf_formatado = formatar_cpf(cpf_limpo)
        self.assertEqual(cpf_formatado, "111.444.777-35")
    
    def test_fluxo_completo_cnpj(self):
        """Testa fluxo completo de validação e formatação de CNPJ."""
        cnpj_entrada = "11.222.333/0001-89"
        
        # Validar
        cnpj_limpo = validar_cnpj(cnpj_entrada)
        self.assertEqual(cnpj_limpo, "11222333000189")
        
        # Formatar
        cnpj_formatado = formatar_cnpj(cnpj_limpo)
        self.assertEqual(cnpj_formatado, "11.222.333/0001-89")