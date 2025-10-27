from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from datetime import datetime, timedelta

# Create your models here.

def get_default_access_until():
    """Return default access until date (November 11, 2025)"""
    return datetime(2025, 11, 11, 23, 59, 59).replace(tzinfo=timezone.get_current_timezone())


class TemporaryClimber(models.Model):
    """Modelo para cadastro temporário de escaladores com acesso até 11/11"""
    
    # Informações básicas
    name = models.CharField(max_length=100, verbose_name="Nome Completo")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    
    # Validação de email
    email_token = models.UUIDField(default=uuid.uuid4, editable=False, verbose_name="Token de Validação")
    email_verified = models.BooleanField(default=False, verbose_name="Email Verificado")
    email_verification_sent = models.DateTimeField(null=True, blank=True, verbose_name="Verificação Enviada")
    email_verified_at = models.DateTimeField(null=True, blank=True, verbose_name="Verificado em")
    
    # Controle de acesso
    access_until = models.DateTimeField(
        default=get_default_access_until,
        verbose_name="Acesso até"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    last_access = models.DateTimeField(null=True, blank=True, verbose_name="Último Acesso")
    access_count = models.IntegerField(default=0, verbose_name="Número de Acessos")
    
    class Meta:
        verbose_name = "Escalador Temporário"
        verbose_name_plural = "Escaladores Temporários"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def has_valid_access(self):
        """Verifica se o escalador tem acesso válido"""
        if not self.is_active:
            return False
        if not self.email_verified:
            return False
        return timezone.now() <= self.access_until
    
    def mark_access(self):
        """Registra um acesso do escalador"""
        self.last_access = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_access', 'access_count'])
    
    def get_verification_url(self, request):
        """Gera URL de verificação de email"""
        from django.urls import reverse
        return request.build_absolute_uri(
            reverse('verify-email', kwargs={'token': str(self.email_token)})
        )
