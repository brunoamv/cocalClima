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
    from django.http import HttpResponse
    
    try:
        # Verify token
        climber = ClimberService.verify_email(token)
        
        if climber:
            # Login the climber
            ClimberService.login_climber(request, climber)
            
            # Return simple success page
            html = f"""
            <!DOCTYPE html>
            <html lang="pt-br">
            <head>
                <meta charset="UTF-8">
                <title>Email Verificado - ClimaCocal</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: green; background: #d4edda; padding: 20px; border-radius: 5px; }}
                    .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="success">
                    <h1>✅ Email Verificado com Sucesso!</h1>
                    <p>Seu email <strong>{climber.email}</strong> foi verificado.</p>
                    <p>Acesso liberado até <strong>11 de Novembro</strong>!</p>
                    <br>
                    <a href="/escaladores/acesso/" class="btn">Acessar Streaming</a>
                    <a href="/" class="btn">Voltar ao Início</a>
                </div>
            </body>
            </html>
            """
            return HttpResponse(html)
        else:
            # Return simple error page
            html = """
            <!DOCTYPE html>
            <html lang="pt-br">
            <head>
                <meta charset="UTF-8">
                <title>Erro na Verificação - ClimaCocal</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .error { color: red; background: #f8d7da; padding: 20px; border-radius: 5px; }
                    .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>❌ Erro na Verificação</h1>
                    <p>Link de verificação inválido ou expirado.</p>
                    <br>
                    <a href="/escaladores/cadastro/" class="btn">Novo Cadastro</a>
                    <a href="/" class="btn">Voltar ao Início</a>
                </div>
            </body>
            </html>
            """
            return HttpResponse(html)
            
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        # Return simple error page
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <title>Erro Interno - ClimaCocal</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: red; background: #f8d7da; padding: 20px; border-radius: 5px; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>❌ Erro Interno</h1>
                <p>Erro na verificação: {str(e)}</p>
                <br>
                <a href="/escaladores/cadastro/" class="btn">Tentar Novamente</a>
                <a href="/" class="btn">Voltar ao Início</a>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)


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
                'Acesso negado. Faça login com seu email verificado.')
            return redirect('climber-login')
        
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
        return redirect('climber-login')


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


def climber_login(request):
    """Login page for verified climbers."""
    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip().lower()
            
            if not email:
                messages.error(request, 'Email é obrigatório.')
                return render(request, 'climber/login.html')
            
            # Find verified climber
            climber = TemporaryClimber.objects.filter(
                email=email,
                email_verified=True
            ).first()
            
            if not climber:
                messages.error(request, 
                    'Email não encontrado ou não verificado. Verifique se você confirmou o email de verificação.')
                return render(request, 'climber/login.html')
            
            # Check if access is still valid
            if not climber.has_access:
                messages.error(request, 
                    'Seu acesso temporário expirou. Entre em contato para renovação.')
                return render(request, 'climber/login.html')
            
            # Login the climber
            ClimberService.login_climber(request, climber)
            messages.success(request, f'Login realizado com sucesso! Bem-vindo, {climber.name}.')
            
            return redirect('climber-access')
            
        except Exception as e:
            logger.error(f"Error in climber login: {e}")
            messages.error(request, 'Erro interno.')
            return render(request, 'climber/login.html')
    
    return render(request, 'climber/login.html')


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