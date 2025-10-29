"""
Service for managing temporary climber registration and email validation.

Handles climber registration, email validation, and temporary access management.
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.cache import cache
from typing import Optional, Dict, Any
from datetime import timedelta
from core.models import TemporaryClimber
import uuid

logger = logging.getLogger(__name__)


class ClimberService:
    """Service for handling temporary climber registration operations."""
    
    @staticmethod
    def register_climber(name: str, email: str, phone: str = "") -> Optional[TemporaryClimber]:
        """
        Register a new climber or return existing one.
        
        Args:
            name: Full name of the climber
            email: Email address
            phone: Optional phone number
            
        Returns:
            TemporaryClimber instance if successful, None otherwise
        """
        try:
            # Check if climber already exists
            existing = TemporaryClimber.objects.filter(email=email).first()
            
            if existing:
                # If email verified and still has access, return existing
                if existing.email_verified and existing.has_access:
                    logger.info(f"Climber already registered with active access: {email}")
                    return existing
                
                # If email verified but access expired, renew access
                elif existing.email_verified and not existing.has_access:
                    logger.info(f"Renewing expired access for climber: {email}")
                    existing.name = name
                    existing.phone = phone
                    existing.access_until = timezone.now() + timedelta(days=30)  # Renew for 30 days
                    existing.email_verified = True  # Keep verified status
                    existing.is_active = True
                    existing.save()
                    return existing
                
                # If not verified, update name and resend verification
                existing.name = name
                existing.phone = phone
                existing.email_token = uuid.uuid4()
                existing.save()
                logger.info(f"Updated existing climber registration: {email}")
                return existing
            
            # Create new climber
            climber = TemporaryClimber.objects.create(
                name=name,
                email=email,
                phone=phone
            )
            logger.info(f"New climber registered: {email}")
            return climber
            
        except Exception as e:
            logger.error(f"Error registering climber: {e}")
            return None
    
    @staticmethod
    def send_verification_email(climber: TemporaryClimber, request) -> bool:
        """
        Send verification email to climber.
        
        Args:
            climber: TemporaryClimber instance
            request: Django HTTP request for building absolute URLs
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Generate verification URL
            verification_url = climber.get_verification_url(request)
            
            # Prepare email context
            context = {
                'climber_name': climber.name,
                'verification_url': verification_url,
                'access_until': climber.access_until.strftime("%d/%m/%Y"),
                'site_name': 'ClimaCocal'
            }
            
            # Render email content
            subject = 'ClimaCocal - Confirme seu email para acesso gratuito'
            html_message = render_to_string('emails/verification_email.html', context)
            plain_message = f"""
            Olá {climber.name}!
            
            Você se cadastrou para acesso gratuito ao ClimaCocal até {context['access_until']}.
            
            Para confirmar seu email e liberar o acesso, clique no link abaixo:
            {verification_url}
            
            ✅ APÓS A VERIFICAÇÃO, ACESSE:
            1. https://climacocal.com.br/escaladores/login/
            2. Digite: {climber.email}
            3. Clique: "Entrar"
            4. Resultado: Redirecionamento automático para página de streaming
            
            Se você não fez esse cadastro, pode ignorar este email.
            
            Atenciosamente,
            Equipe ClimaCocal
            """
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@climacocal.com.br'),
                recipient_list=[climber.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Update sent timestamp
            climber.email_verification_sent = timezone.now()
            climber.save(update_fields=['email_verification_sent'])
            
            logger.info(f"Verification email sent to: {climber.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return False
    
    @staticmethod
    def verify_email(token: str) -> Optional[TemporaryClimber]:
        """
        Verify climber email using token.
        
        Args:
            token: UUID token for verification
            
        Returns:
            TemporaryClimber instance if verified, None otherwise
        """
        try:
            # First, check if token exists at all
            climber = TemporaryClimber.objects.filter(email_token=token).first()
            
            if not climber:
                logger.warning(f"Invalid verification token: {token}")
                return None
            
            # Check if already verified
            if climber.email_verified:
                logger.info(f"Email already verified for climber: {climber.email}")
                return climber  # Return the climber to show success page
            
            # Mark as verified
            climber.email_verified = True
            climber.email_verified_at = timezone.now()
            climber.save(update_fields=['email_verified', 'email_verified_at'])
            
            logger.info(f"Email verified for climber: {climber.email}")
            return climber
            
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return None
    
    @staticmethod
    def check_climber_access(request) -> bool:
        """
        Check if current session has valid climber access.
        
        Args:
            request: Django HTTP request
            
        Returns:
            True if has valid access, False otherwise
        """
        try:
            # Check session for climber ID
            climber_id = request.session.get('climber_id')
            if not climber_id:
                return False
            
            # Check cache first (for performance)
            cache_key = f"climber_access_{climber_id}"
            cached_access = cache.get(cache_key)
            if cached_access is not None:
                return cached_access
            
            # Check database
            climber = TemporaryClimber.objects.filter(id=climber_id).first()
            if not climber:
                return False
            
            # Check access validity
            has_access = climber.has_valid_access()
            
            # Cache result for 5 minutes
            cache.set(cache_key, has_access, timeout=300)
            
            # Mark access if valid
            if has_access:
                climber.mark_access()
            
            return has_access
            
        except Exception as e:
            logger.error(f"Error checking climber access: {e}")
            return False
    
    @staticmethod
    def login_climber(request, climber: TemporaryClimber) -> None:
        """
        Login a climber by setting session data.
        
        Args:
            request: Django HTTP request
            climber: TemporaryClimber instance
        """
        request.session['climber_id'] = climber.id
        request.session['climber_email'] = climber.email
        request.session['climber_name'] = climber.name
        request.session['climber_access_until'] = climber.access_until.isoformat()
        logger.info(f"Climber logged in: {climber.email}")
    
    @staticmethod
    def logout_climber(request) -> None:
        """
        Logout a climber by clearing session data.
        
        Args:
            request: Django HTTP request
        """
        climber_email = request.session.get('climber_email', 'unknown')
        
        # Clear session
        request.session.pop('climber_id', None)
        request.session.pop('climber_email', None)
        request.session.pop('climber_name', None)
        request.session.pop('climber_access_until', None)
        
        # Clear cache
        climber_id = request.session.get('climber_id')
        if climber_id:
            cache.delete(f"climber_access_{climber_id}")
        
        logger.info(f"Climber logged out: {climber_email}")
    
    @staticmethod
    def get_climber_stats() -> Dict[str, Any]:
        """
        Get statistics about climber registrations.
        
        Returns:
            Dictionary with climber statistics
        """
        try:
            total = TemporaryClimber.objects.count()
            verified = TemporaryClimber.objects.filter(email_verified=True).count()
            active = TemporaryClimber.objects.filter(
                email_verified=True,
                is_active=True,
                access_until__gt=timezone.now()
            ).count()
            
            return {
                'total_registered': total,
                'total_verified': verified,
                'currently_active': active,
                'pending_verification': total - verified
            }
            
        except Exception as e:
            logger.error(f"Error getting climber stats: {e}")
            return {
                'total_registered': 0,
                'total_verified': 0,
                'currently_active': 0,
                'pending_verification': 0
            }
    
    @staticmethod
    def renew_climber_access(email: str, days: int = 30) -> bool:
        """
        Renew access for an existing climber.
        
        Args:
            email: Climber's email address
            days: Number of days to extend access (default: 30)
            
        Returns:
            True if renewal successful, False otherwise
        """
        try:
            climber = TemporaryClimber.objects.filter(email=email).first()
            
            if not climber:
                logger.error(f"Climber not found for renewal: {email}")
                return False
            
            # Renew access from now or extend current access if still active
            if climber.has_access:
                # Extend current access
                climber.access_until = climber.access_until + timedelta(days=days)
                logger.info(f"Extended access for {email} by {days} days")
            else:
                # Renew from now
                climber.access_until = timezone.now() + timedelta(days=days)
                logger.info(f"Renewed access for {email} for {days} days")
            
            climber.is_active = True
            climber.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error renewing climber access for {email}: {e}")
            return False
    
    @staticmethod
    def get_expired_climbers():
        """
        Get list of climbers with expired access.
        
        Returns:
            QuerySet of expired climbers
        """
        return TemporaryClimber.objects.filter(
            email_verified=True,
            access_until__lt=timezone.now()
        ).order_by('-access_until')