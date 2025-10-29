from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta

def get_default_access_until():
    """Retorna a data/hora padrão para expiração do acesso (11/11/2025 às 23:59)"""
    from datetime import datetime
    # Acesso até 11 de novembro de 2025 às 23:59 (horário de Brasília)
    return datetime(2025, 11, 11, 23, 59, 59, tzinfo=timezone.utc)

class TemporaryClimber(models.Model):
    """
    Modelo para escaladores temporários com acesso limitado por tempo
    """
    name = models.CharField('Nome Completo', max_length=100)
    email = models.EmailField('Email', unique=True)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    
    # Verificação de email
    email_token = models.UUIDField('Token de Validação', default=uuid.uuid4, editable=False)
    email_verified = models.BooleanField('Email Verificado', default=False)
    email_verification_sent = models.DateTimeField('Verificação Enviada', null=True, blank=True)
    email_verified_at = models.DateTimeField('Verificado em', null=True, blank=True)
    
    # Controle de acesso
    access_until = models.DateTimeField('Acesso até', default=get_default_access_until)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    last_access = models.DateTimeField('Último Acesso', null=True, blank=True)
    access_count = models.IntegerField('Número de Acessos', default=0)
    
    class Meta:
        verbose_name = 'Escalador Temporário'
        verbose_name_plural = 'Escaladores Temporários'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} ({self.email})'
    
    @property
    def has_access(self):
        """Verifica se o escalador ainda tem acesso válido"""
        return (
            self.is_active and 
            self.email_verified and 
            self.access_until > timezone.now()
        )
    
    def has_valid_access(self):
        """Método para compatibilidade com ClimberService"""
        return self.has_access
    
    def mark_access(self):
        """Marca um acesso ao sistema"""
        self.last_access = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_access', 'access_count'])
    
    def get_verification_url(self, request):
        """Gera URL de verificação de email"""
        from django.urls import reverse
        return request.build_absolute_uri(
            reverse('verify-email', kwargs={'token': str(self.email_token)})
        )

# Create your models here.
