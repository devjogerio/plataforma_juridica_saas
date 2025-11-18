"""
Factories para geração de dados de teste usando Factory Boy
"""
import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, Sequence
from django.contrib.auth import get_user_model
from datetime import date, timedelta
import random

from clientes.models import Cliente, InteracaoCliente
from processos.models import Processo, Andamento, Prazo
from documentos.models import Documento, TipoDocumento
from usuarios.models import Usuario
from configuracoes.models import TipoProcesso, AreaDireito, StatusProcesso

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory para criação de usuários"""
    
    class Meta:
        model = User
    
    username = Sequence(lambda n: f"user{n}")
    email = Faker('email')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    is_active = True
    is_staff = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Define senha padrão para usuários de teste"""
        if not create:
            return
        
        password = extracted or 'testpass123'
        self.set_password(password)
        self.save()


class AdminUserFactory(UserFactory):
    """Factory para usuários administradores"""
    
    is_staff = True
    is_superuser = True
    username = Sequence(lambda n: f"admin{n}")


class ClienteFactory(DjangoModelFactory):
    """Factory para criação de clientes"""
    
    class Meta:
        model = Cliente
        skip_postgeneration_save = True
    
    nome_razao_social = Faker('company')
    tipo_pessoa = 'PF'  # Fixo como pessoa física para simplificar
    cpf_cnpj = Sequence(lambda n: f"11144477{n:03d}")
    email = Faker('email')
    telefone = factory.LazyAttribute(lambda obj: '(11) 99999-9999')
    endereco = Faker('address')
    cidade = Faker('city')
    estado = factory.Iterator(['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'GO'])
    cep = Faker('postcode')
    ativo = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override para desabilitar validação durante criação."""
        instance = model_class(*args, **kwargs)
        instance._skip_validation = True
        instance.save()
        return instance
    
    class Params:
        """Parâmetros para diferentes tipos de clientes"""
        pessoa_fisica = factory.Trait(
            tipo_pessoa='PF',
            nome_razao_social=Faker('name'),
            cpf_cnpj="11144477735"  # CPF válido conhecido
        )
        pessoa_juridica = factory.Trait(
            tipo_pessoa='PJ',
            nome_razao_social=Faker('company'),
            cpf_cnpj="11222333000189"  # CNPJ válido conhecido
        )
        inativo = factory.Trait(
            ativo=False
        )


class InteracaoClienteFactory(DjangoModelFactory):
    """Factory para interações com clientes"""
    
    class Meta:
        model = InteracaoCliente
    
    cliente = SubFactory(ClienteFactory)
    usuario = SubFactory(UserFactory)
    tipo_interacao = factory.Iterator(['email', 'telefone', 'reuniao', 'whatsapp'])
    descricao = Faker('text', max_nb_chars=500)
    data_interacao = Faker('date_between', start_date='-30d', end_date='today')


class TipoProcessoFactory(DjangoModelFactory):
    """Factory para tipos de processo"""
    
    class Meta:
        model = TipoProcesso
    
    nome = Faker('word')
    codigo = Faker('lexify', text='???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    descricao = Faker('text', max_nb_chars=200)
    cor = Faker('hex_color')
    icone = 'bi-folder'
    ativo = True
    ordem = Faker('random_int', min=0, max=100)


class AreaDireitoFactory(DjangoModelFactory):
    """Factory para áreas do direito"""
    
    class Meta:
        model = AreaDireito
    
    nome = Faker('word')
    codigo = Faker('lexify', text='???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    descricao = Faker('text', max_nb_chars=200)
    cor = Faker('hex_color')
    icone = 'bi-scales'
    ativo = True
    ordem = Faker('random_int', min=0, max=100)


class StatusProcessoFactory(DjangoModelFactory):
    """Factory para status de processo"""
    
    class Meta:
        model = StatusProcesso
    
    nome = Faker('word')
    codigo = Faker('lexify', text='???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    descricao = Faker('text', max_nb_chars=200)
    cor = Faker('hex_color')
    icone = 'bi-circle'
    is_inicial = False
    is_final = False
    permite_edicao = True
    ativo = True
    ordem = Faker('random_int', min=0, max=100)


class ProcessoFactory(DjangoModelFactory):
    """Factory para criação de processos"""
    
    class Meta:
        model = Processo
    
    numero_processo = Sequence(lambda n: f"1234567-{n:02d}.2024.8.26.0001")
    tipo_processo = factory.Iterator(['Cível', 'Trabalhista', 'Criminal', 'Tributário'])
    area_direito = factory.Iterator(['Civil', 'Trabalhista', 'Penal', 'Tributário'])
    status = factory.Iterator(['ativo', 'suspenso', 'arquivado', 'encerrado'])
    valor_causa = Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    comarca_tribunal = Faker('city')
    vara_orgao = Faker('random_element', elements=['1ª Vara Cível', '2ª Vara Cível', 'Vara do Trabalho'])
    data_inicio = Faker('date_between', start_date='-2y', end_date='today')
    cliente = SubFactory(ClienteFactory)
    usuario_responsavel = SubFactory(UserFactory)
    observacoes = Faker('text', max_nb_chars=1000)
    
    class Params:
        """Parâmetros para diferentes tipos de processos"""
        ativo = factory.Trait(
            status='ativo',
            data_encerramento=None
        )
        encerrado = factory.Trait(
            status='encerrado',
            data_encerramento=Faker('date_between', start_date='-1y', end_date='today')
        )
        alto_valor = factory.Trait(
            valor_causa=Faker('pydecimal', left_digits=7, right_digits=2, positive=True)
        )


class AndamentoFactory(DjangoModelFactory):
    """Factory para andamentos de processos"""
    
    class Meta:
        model = Andamento
    
    processo = SubFactory(ProcessoFactory)
    data_andamento = Faker('date_between', start_date='-30d', end_date='today')
    tipo_andamento = factory.Iterator([
        'Petição Inicial', 'Citação', 'Contestação', 'Audiência', 
        'Sentença', 'Recurso', 'Despacho'
    ])
    descricao = Faker('text', max_nb_chars=1000)
    usuario = SubFactory(UserFactory)


class PrazoFactory(DjangoModelFactory):
    """Factory para prazos"""
    
    class Meta:
        model = Prazo
    
    processo = SubFactory(ProcessoFactory)
    tipo_prazo = Faker('random_element', elements=['contestacao', 'recurso', 'manifestacao'])
    data_limite = Faker('future_date', end_date='+30d')
    descricao = Faker('text', max_nb_chars=200)
    usuario_responsavel = SubFactory(UserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        dv = kwargs.pop('data_vencimento', None)
        if dv and 'data_limite' not in kwargs:
            kwargs['data_limite'] = dv
        resp = kwargs.pop('responsavel', None)
        if resp and 'usuario_responsavel' not in kwargs:
            kwargs['usuario_responsavel'] = resp
        return super()._create(model_class, *args, **kwargs)


class TipoDocumentoFactory(DjangoModelFactory):
    """Factory para tipos de documento"""
    
    class Meta:
        model = 'documentos.TipoDocumento'
    
    nome = Faker('word')
    descricao = Faker('text', max_nb_chars=100)


class DocumentoFactory(DjangoModelFactory):
    """Factory para documentos"""
    
    class Meta:
        model = Documento
    
    nome_arquivo = Faker('file_name', extension='pdf')
    descricao = Faker('text', max_nb_chars=200)
    processo = SubFactory(ProcessoFactory)
    tipo_documento = SubFactory(TipoDocumentoFactory)
    usuario_upload = SubFactory(UserFactory)
    arquivo = factory.django.FileField(filename='test_document.pdf')
    tamanho_arquivo = 1024
    hash_arquivo = Faker('sha256')
    extensao = 'pdf'
    
    class Params:
        """Parâmetros para diferentes tipos de documentos"""
        imagem = factory.Trait(
            nome_arquivo=Faker('file_name', extension='jpg'),
            arquivo=factory.django.ImageField(filename='test_image.jpg'),
            extensao='jpg'
        )

    @factory.post_generation
    def nome(self, create, extracted, **kwargs):
        if extracted:
            self.nome_arquivo = extracted
            if create:
                self.save(update_fields=['nome_arquivo'])

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        nome = kwargs.pop('nome', None)
        if nome and 'nome_arquivo' not in kwargs:
            kwargs['nome_arquivo'] = nome
        tipo = kwargs.get('tipo_documento')
        if isinstance(tipo, str):
            from documentos.models import TipoDocumento
            tipo_obj, _ = TipoDocumento.objects.get_or_create(nome=tipo)
            kwargs['tipo_documento'] = tipo_obj
        arquivo = kwargs.get('arquivo')
        if isinstance(arquivo, str):
            from django.core.files.base import ContentFile
            kwargs['arquivo'] = ContentFile(b'', name=arquivo)
        return super()._create(model_class, *args, **kwargs)


# Factories para cenários específicos de teste
class ProcessoCompletoFactory(ProcessoFactory):
    """Factory que cria um processo com todos os relacionamentos"""
    
    @factory.post_generation
    def create_related(self, create, extracted, **kwargs):
        """Cria objetos relacionados após a criação do processo"""
        if not create:
            return
        
        # Criar andamentos
        AndamentoFactory.create_batch(3, processo=self)
        
        # Criar prazos
        PrazoFactory.create_batch(2, processo=self)
        
        # Criar documentos
        DocumentoFactory.create_batch(2, processo=self)


class ClienteCompletoFactory(ClienteFactory):
    """Factory que cria um cliente com processos e interações"""
    
    @factory.post_generation
    def create_related(self, create, extracted, **kwargs):
        """Cria objetos relacionados após a criação do cliente"""
        if not create:
            return
        
        # Criar processos
        ProcessoFactory.create_batch(2, cliente=self)
        
        # Criar interações
        InteracaoClienteFactory.create_batch(3, cliente=self)


# Mixins para reutilização
class TimestampMixin:
    """Mixin para campos de timestamp"""
    created_at = Faker('date_time_between', start_date='-1y', end_date='now')
    updated_at = LazyAttribute(lambda obj: obj.created_at + timedelta(days=random.randint(0, 30)))


class AuditMixin:
    """Mixin para campos de auditoria"""
    usuario_criacao = SubFactory(UserFactory)
    usuario_atualizacao = SubFactory(UserFactory)
