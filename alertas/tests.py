from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Alerta, ConfiguracaoAlerta, TipoAlerta, PrioridadeAlerta, StatusAlerta

User = get_user_model()


class AlertaModelTest(TestCase):
    """Testes para o modelo Alerta"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.alerta = Alerta.objects.create(
            usuario=self.user,
            titulo='Teste Alerta',
            descricao='Descrição do teste',
            tipo=TipoAlerta.LEMBRETE,
            prioridade=PrioridadeAlerta.MEDIA,
            data_alerta=timezone.now() + timedelta(hours=1)
        )
    
    def test_alerta_creation(self):
        """Testa a criação de um alerta"""
        self.assertEqual(self.alerta.titulo, 'Teste Alerta')
        self.assertEqual(self.alerta.usuario, self.user)
        self.assertEqual(self.alerta.status, StatusAlerta.ATIVO)
    
    def test_marcar_como_concluido(self):
        """Testa marcar alerta como concluído"""
        self.alerta.marcar_como_concluido()
        self.assertEqual(self.alerta.status, StatusAlerta.CONCLUIDO)
        self.assertIsNotNone(self.alerta.concluido_em)
    
    def test_cancelar_alerta(self):
        """Testa cancelar alerta"""
        self.alerta.cancelar()
        self.assertEqual(self.alerta.status, StatusAlerta.CANCELADO)
    
    def test_adiar_alerta(self):
        """Testa adiar alerta"""
        nova_data = timezone.now() + timedelta(days=1)
        self.alerta.adiar(nova_data)
        self.assertEqual(self.alerta.data_alerta, nova_data)
        self.assertEqual(self.alerta.status, StatusAlerta.ADIADO)


class ConfiguracaoAlertaModelTest(TestCase):
    """Testes para o modelo ConfiguracaoAlerta"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_configuracao_creation(self):
        """Testa a criação de configuração de alerta"""
        config = ConfiguracaoAlerta.objects.create(usuario=self.user)
        self.assertEqual(config.usuario, self.user)
        self.assertTrue(config.alertas_ativos)
        self.assertEqual(config.antecedencia_padrao, 60)