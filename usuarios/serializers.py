from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Usuario

User = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer básico para usuário (sem dados sensíveis)"""
    nome_completo = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'nome_completo', 'is_active', 'date_joined'
        ]


class UsuarioDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes completos do usuário"""
    nome_completo = serializers.CharField(source='get_full_name', read_only=True)
    grupos = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'nome_completo', 'oab_numero', 'oab_uf', 'telefone',
            'cargo', 'departamento', 'is_active', 'is_staff',
            'date_joined', 'last_login', 'grupos'
        ]


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de usuários"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'oab_numero', 'oab_uf',
            'telefone', 'cargo', 'departamento', 'is_active', 'is_staff'
        ]
    
    def validate_username(self, value):
        """Validar username único"""
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Já existe um usuário com este nome de usuário."
            )
        return value
    
    def validate_email(self, value):
        """Validar email único"""
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Já existe um usuário com este e-mail."
            )
        return value
    
    def validate_oab_numero(self, value):
        """Validar número da OAB único"""
        if value and Usuario.objects.filter(oab_numero=value).exists():
            raise serializers.ValidationError(
                "Já existe um usuário com este número da OAB."
            )
        return value
    
    def validate(self, data):
        """Validar senhas"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                "As senhas não coincidem."
            )
        return data
    
    def create(self, validated_data):
        """Criar usuário com senha criptografada"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = Usuario.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de usuários"""
    
    class Meta:
        model = Usuario
        fields = [
            'email', 'first_name', 'last_name', 'oab_numero', 'oab_uf',
            'telefone', 'cargo', 'departamento', 'is_active', 'is_staff'
        ]
    
    def validate_email(self, value):
        """Validar email único (exceto para o próprio usuário)"""
        queryset = Usuario.objects.filter(email=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um usuário com este e-mail."
            )
        return value
    
    def validate_oab_numero(self, value):
        """Validar número da OAB único (exceto para o próprio usuário)"""
        if not value:
            return value
        
        queryset = Usuario.objects.filter(oab_numero=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um usuário com este número da OAB."
            )
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para alteração de senha"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        """Validar senha atual"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Senha atual incorreta."
            )
        return value
    
    def validate(self, data):
        """Validar nova senha"""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError(
                "As novas senhas não coincidem."
            )
        return data
    
    def save(self):
        """Alterar senha do usuário"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        """Validar credenciais"""
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    "Credenciais inválidas."
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    "Conta desativada."
                )
            
            data['user'] = user
        else:
            raise serializers.ValidationError(
                "Username e senha são obrigatórios."
            )
        
        return data


class PerfilSerializer(serializers.ModelSerializer):
    """Serializer para perfil do usuário logado"""
    nome_completo = serializers.CharField(source='get_full_name', read_only=True)
    grupos = serializers.StringRelatedField(many=True, read_only=True)
    
    # Estatísticas do usuário
    total_processos = serializers.IntegerField(read_only=True)
    processos_ativos = serializers.IntegerField(read_only=True)
    prazos_pendentes = serializers.IntegerField(read_only=True)
    andamentos_mes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'nome_completo', 'oab_numero', 'oab_uf', 'telefone',
            'cargo', 'departamento', 'is_active', 'date_joined',
            'last_login', 'grupos', 'total_processos', 'processos_ativos',
            'prazos_pendentes', 'andamentos_mes'
        ]
        read_only_fields = ['username', 'is_active', 'date_joined', 'last_login']


class UsuarioStatisticsSerializer(serializers.Serializer):
    """Serializer para estatísticas de usuários"""
    total_usuarios = serializers.IntegerField()
    usuarios_ativos = serializers.IntegerField()
    usuarios_inativos = serializers.IntegerField()
    usuarios_staff = serializers.IntegerField()
    usuarios_mes_atual = serializers.IntegerField()
    
    # Por cargo
    por_cargo = serializers.DictField()
    
    # Por departamento
    por_departamento = serializers.DictField()
    
    # Usuários mais ativos (por andamentos)
    usuarios_mais_ativos = serializers.ListField()


class UsuarioResumoSerializer(serializers.ModelSerializer):
    """Serializer resumido para uso em outros endpoints"""
    nome_completo = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'nome_completo', 'email',
            'cargo', 'is_active'
        ]


class TokenResponseSerializer(serializers.Serializer):
    """Serializer para resposta de token JWT"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UsuarioSerializer()
    expires_in = serializers.IntegerField()


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer para refresh token"""
    refresh = serializers.CharField()
    
    def validate_refresh(self, value):
        """Validar refresh token"""
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        try:
            RefreshToken(value)
        except TokenError:
            raise serializers.ValidationError(
                "Token inválido ou expirado."
            )
        
        return value