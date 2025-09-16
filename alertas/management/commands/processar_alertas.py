from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from alertas.services import AlertaService
from alertas.models import Alerta, StatusAlerta
from notificacoes.services import NotificacaoService
from notificacoes.models import TipoNotificacao, PrioridadeNotificacao


class Command(BaseCommand):
    """Comando para processar alertas recorrentes e notificar sobre vencidos"""
    
    help = 'Processa alertas recorrentes e envia notificações sobre alertas vencidos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações no banco de dados',
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibe informações detalhadas',
        )
    
    def handle(self, *args, **options):
        """Executa o processamento de alertas"""
        
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS(f'Iniciando processamento de alertas - {timezone.now()}')
            )
        
        # Processar alertas recorrentes
        alertas_recorrentes_criados = 0
        if not dry_run:
            alertas_recorrentes_criados = AlertaService.processar_alertas_recorrentes()
        else:
            # Contar quantos seriam criados
            alertas_recorrentes = Alerta.objects.filter(
                recorrente=True,
                status=StatusAlerta.ATIVO,
                data_alerta__lt=timezone.now()
            )
            alertas_recorrentes_criados = alertas_recorrentes.count()
        
        if verbose and alertas_recorrentes_criados > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Alertas recorrentes processados: {alertas_recorrentes_criados}')
            )
        
        # Processar alertas vencidos
        alertas_vencidos = self._processar_alertas_vencidos(dry_run, verbose)
        
        # Processar alertas próximos (notificação prévia)
        alertas_proximos = self._processar_alertas_proximos(dry_run, verbose)
        
        # Resumo final
        self.stdout.write(
            self.style.SUCCESS(
                f'Processamento concluído:\n'
                f'- Alertas recorrentes criados: {alertas_recorrentes_criados}\n'
                f'- Alertas vencidos notificados: {alertas_vencidos}\n'
                f'- Alertas próximos notificados: {alertas_proximos}'
            )
        )
    
    def _processar_alertas_vencidos(self, dry_run: bool, verbose: bool) -> int:
        """Processa alertas vencidos e envia notificações"""
        
        # Buscar alertas vencidos que ainda não foram notificados
        alertas_vencidos = Alerta.objects.filter(
            status=StatusAlerta.ATIVO,
            data_vencimento__lt=timezone.now(),
            notificado_vencimento=False
        ).select_related('usuario')
        
        count = 0
        
        for alerta in alertas_vencidos:
            if verbose:
                self.stdout.write(
                    f'Processando alerta vencido: {alerta.titulo} (usuário: {alerta.usuario.username})'
                )
            
            if not dry_run:
                # Criar notificação de vencimento
                NotificacaoService.criar_notificacao(
                    usuario=alerta.usuario,
                    titulo=f"⚠️ Alerta Vencido",
                    mensagem=f"O alerta '{alerta.titulo}' venceu em {alerta.data_vencimento.strftime('%d/%m/%Y %H:%M')}.",
                    tipo=TipoNotificacao.ALERTA,
                    prioridade=PrioridadeNotificacao.ALTA,
                    url_acao=alerta.url_acao
                )
                
                # Marcar como notificado
                alerta.notificado_vencimento = True
                alerta.save()
            
            count += 1
        
        return count
    
    def _processar_alertas_proximos(self, dry_run: bool, verbose: bool) -> int:
        """Processa alertas próximos e envia notificações de antecedência"""
        
        agora = timezone.now()
        
        # Buscar alertas que devem ser notificados baseado na antecedência
        alertas_proximos = Alerta.objects.filter(
            status=StatusAlerta.ATIVO,
            notificado_antecedencia=False
        ).select_related('usuario')
        
        count = 0
        
        for alerta in alertas_proximos:
            # Calcular quando deve ser notificado
            tempo_notificacao = alerta.data_alerta - timedelta(minutes=alerta.antecedencia_minutos)
            
            # Se já passou do tempo de notificação
            if agora >= tempo_notificacao:
                if verbose:
                    self.stdout.write(
                        f'Processando alerta próximo: {alerta.titulo} (usuário: {alerta.usuario.username})'
                    )
                
                if not dry_run:
                    # Criar notificação de antecedência
                    NotificacaoService.criar_notificacao(
                        usuario=alerta.usuario,
                        titulo=f"🔔 {alerta.titulo}",
                        mensagem=f"{alerta.descricao}\nData: {alerta.data_alerta.strftime('%d/%m/%Y %H:%M')}",
                        tipo=TipoNotificacao.LEMBRETE,
                        prioridade=self._mapear_prioridade_alerta(alerta.prioridade),
                        url_acao=alerta.url_acao
                    )
                    
                    # Marcar como notificado
                    alerta.notificado_antecedencia = True
                    alerta.save()
                
                count += 1
        
        return count
    
    def _mapear_prioridade_alerta(self, prioridade_alerta: str) -> str:
        """Mapeia prioridade do alerta para prioridade da notificação"""
        
        mapeamento = {
            'critica': PrioridadeNotificacao.CRITICA,
            'alta': PrioridadeNotificacao.ALTA,
            'media': PrioridadeNotificacao.MEDIA,
            'baixa': PrioridadeNotificacao.BAIXA,
        }
        
        return mapeamento.get(prioridade_alerta, PrioridadeNotificacao.MEDIA)