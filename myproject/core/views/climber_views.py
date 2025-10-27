"""
Climber registration and access views.

Handles temporary climber registration, email verification, and access management.
"""

import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse

from core.models import TemporaryClimber
from core.services.climber_service import ClimberService

logger = logging.getLogger(__name__)


def climber_register(request):
    """Render climber registration page."""
    if request.method == 'GET':
        return render(request, 'climber/register.html')
    
    elif request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            phone = request.POST.get('phone', '').strip()
            
            # Validation
            if not name or not email:
                messages.error(request, 'Nome e email são obrigatórios.')
                return render(request, 'climber/register.html')
            
            if len(name) < 3:
                messages.error(request, 'Nome deve ter pelo menos 3 caracteres.')
                return render(request, 'climber/register.html')
            
            # Email format validation
            if '@' not in email or '.' not in email:
                messages.error(request, 'Formato de email inválido.')
                return render(request, 'climber/register.html')
            
            # Check if email already exists and is verified
            existing = TemporaryClimber.objects.filter(email=email, email_verified=True).first()
            if existing:
                messages.error(request, 'Email já cadastrado e verificado.')
                return render(request, 'climber/register.html')
            
            # Register climber
            climber = ClimberService.register_climber(name, email, phone)
            
            if not climber:
                messages.error(request, 'Erro interno. Tente novamente.')
                return render(request, 'climber/register.html')
            
            # Send verification email
            email_sent = ClimberService.send_verification_email(climber, request)
            
            if email_sent:
                messages.success(request, 
                    f'Cadastro realizado! Verifique seu email ({email}) para ativar o acesso.')
                return render(request, 'climber/register_success.html', {
                    'climber': climber,
                    'email': email
                })
            else:
                messages.error(request, 
                    'Cadastro realizado, mas houve erro no envio do email. '
                    'Contate o suporte.')
                return render(request, 'climber/register.html')
                
        except Exception as e:
            logger.error(f"Error in climber registration: {e}")
            messages.error(request, 'Erro interno. Tente novamente.')
            return render(request, 'climber/register.html')


def verify_email(request, token):
    """Verify climber email using token."""
    try:
        # Verify token
        climber = ClimberService.verify_email(token)
        
        if climber:
            # Login the climber
            ClimberService.login_climber(request, climber)
            
            messages.success(request, 
                f'Email verificado com sucesso! Acesso liberado até 11/11.')
            
            return render(request, 'climber/email_verified.html', {
                'climber': climber,
                'access_until': climber.access_until
            })
        else:
            messages.error(request, 
                'Link de verificação inválido ou expirado.')
            return render(request, 'climber/verification_error.html')
            
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        messages.error(request, 'Erro interno na verificação.')
        return render(request, 'climber/verification_error.html')


def climber_status(request):
    """API endpoint to check climber access status."""
    try:
        # Check if climber is logged in
        has_access = ClimberService.check_climber_access(request)
        
        if has_access:
            climber_name = request.session.get('climber_name', 'Escalador')
            access_until = request.session.get('climber_access_until')
            
            return JsonResponse({
                'has_access': True,
                'climber_type': 'temporary',
                'climber_name': climber_name,
                'access_until': access_until,
                'message': f'Acesso liberado para {climber_name} até 11/11'
            })
        else:
            return JsonResponse({
                'has_access': False,
                'climber_type': None,
                'message': 'Acesso temporário não encontrado'
            })
            
    except Exception as e:
        logger.error(f"Error checking climber status: {e}")
        return JsonResponse({
            'has_access': False,
            'climber_type': None,
            'message': 'Erro ao verificar acesso'
        }, status=500)


def climber_access(request):
    """Main access page for verified climbers."""
    try:
        # Check access
        has_access = ClimberService.check_climber_access(request)
        
        if not has_access:
            messages.error(request, 
                'Acesso negado. Faça o cadastro ou verifique seu email.')
            return redirect('climber-register')
        
        # Get climber info from session
        climber_name = request.session.get('climber_name', 'Escalador')
        access_until = request.session.get('climber_access_until')
        
        return render(request, 'climber/access.html', {
            'climber_name': climber_name,
            'access_until': access_until
        })
        
    except Exception as e:
        logger.error(f"Error in climber access: {e}")
        messages.error(request, 'Erro interno.')
        return redirect('climber-register')


def climber_logout(request):
    """Logout climber and redirect to homepage."""
    ClimberService.logout_climber(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('home')


@require_http_methods(["GET"])
def climber_admin_stats(request):
    """Admin endpoint for climber statistics."""
    try:
        # Simple admin check (you can improve this with proper authentication)
        if not request.user.is_staff:
            raise Http404()
        
        stats = ClimberService.get_climber_stats()
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'timestamp': timezone.now().isoformat()
        })
        
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error getting climber stats: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno'
        }, status=500)


def resend_verification(request):
    """Resend verification email for unverified climbers."""
    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip().lower()
            
            if not email:
                messages.error(request, 'Email é obrigatório.')
                return render(request, 'climber/resend_verification.html')
            
            # Find unverified climber
            climber = TemporaryClimber.objects.filter(
                email=email,
                email_verified=False
            ).first()
            
            if not climber:
                messages.error(request, 
                    'Email não encontrado ou já verificado.')
                return render(request, 'climber/resend_verification.html')
            
            # Send verification email
            email_sent = ClimberService.send_verification_email(climber, request)
            
            if email_sent:
                messages.success(request, 
                    f'Email de verificação reenviado para {email}.')
            else:
                messages.error(request, 
                    'Erro ao reenviar email. Tente novamente.')
                
            return render(request, 'climber/resend_verification.html')
            
        except Exception as e:
            logger.error(f"Error resending verification: {e}")
            messages.error(request, 'Erro interno.')
            return render(request, 'climber/resend_verification.html')
    
    return render(request, 'climber/resend_verification.html')