#!/usr/bin/env python3
"""
TESTE CRÍTICO: Validação do Fix de Verificação de Email
Verifica se o sistema de verificação está funcionando após o fix na função get_default_access_until()
"""
import sys
import os
sys.path.append('/app')

import django
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from core.models import get_default_access_until, TemporaryClimber
from core.services.climber_service import ClimberService
from django.utils import timezone
import traceback
import uuid

def test_verification_system():
    """Testa o sistema de verificação completo"""
    
    print('🚨 TESTE CRÍTICO: Verificação de Email em Produção')
    print('=' * 60)
    print('Testando fix: timezone.datetime → datetime na função get_default_access_until()')
    print()
    
    test_passed = 0
    test_total = 0
    
    # Teste 1: Função get_default_access_until
    test_total += 1
    try:
        print('1. Testando função get_default_access_until()...')
        default_date = get_default_access_until()
        expected_date = "2025-11-11 23:59:59"
        
        print(f'   ✅ Data padrão: {default_date}')
        print(f'   ✅ Timezone: {default_date.tzinfo}')
        print(f'   ✅ Data esperada: {expected_date}')
        
        if "2025-11-11" in str(default_date):
            print('   ✅ PASSOU: Data correta (11/11/2025)')
            test_passed += 1
        else:
            print(f'   ❌ FALHOU: Data incorreta: {default_date}')
            
    except Exception as e:
        print(f'   ❌ ERRO na função get_default_access_until: {str(e)}')
        print(f'   Traceback: {traceback.format_exc()}')
    
    # Teste 2: Criação de escalador
    test_total += 1
    escalador = None
    try:
        print('\n2. Testando criação de escalador temporário...')
        test_email = f'teste.fix.{uuid.uuid4().hex[:8]}@exemplo.com'
        
        escalador = ClimberService.register_climber(
            name='Teste Fix Verificação', 
            email=test_email, 
            phone='61999999999'
        )
        
        if escalador:
            print(f'   ✅ Escalador criado: {escalador.name}')
            print(f'   ✅ Email: {escalador.email}')
            print(f'   ✅ Token: {escalador.email_token}')
            print(f'   ✅ Acesso até: {escalador.access_until}')
            print(f'   ✅ Email verificado: {escalador.email_verified}')
            
            # Verifica se a data está correta
            if "2025-11-11" in str(escalador.access_until):
                print('   ✅ PASSOU: Data de acesso correta')
                test_passed += 1
            else:
                print(f'   ❌ FALHOU: Data de acesso incorreta: {escalador.access_until}')
        else:
            print('   ❌ FALHOU: Não foi possível criar escalador')
            
    except Exception as e:
        print(f'   ❌ ERRO na criação do escalador: {str(e)}')
        print(f'   Traceback: {traceback.format_exc()}')
    
    # Teste 3: Verificação de email
    test_total += 1
    try:
        if escalador:
            print('\n3. Testando verificação de email...')
            token = str(escalador.email_token)
            
            escalador_verificado = ClimberService.verify_email(token)
            
            if escalador_verificado:
                print(f'   ✅ Verificação OK: {escalador_verificado.email_verified}')
                print(f'   ✅ Verificado em: {escalador_verificado.email_verified_at}')
                print('   ✅ PASSOU: Sistema de verificação funcionando')
                test_passed += 1
            else:
                print('   ❌ FALHOU: Falha na verificação de email')
        else:
            print('\n3. ❌ PULADO: Teste de verificação (escalador não criado)')
            
    except Exception as e:
        print(f'   ❌ ERRO na verificação: {str(e)}')
        print(f'   Traceback: {traceback.format_exc()}')
    
    # Limpeza
    try:
        if escalador:
            escalador.delete()
            print('\n   ✅ Teste limpo da base de dados')
    except Exception as e:
        print(f'\n   ⚠️ Aviso: Erro na limpeza: {str(e)}')
    
    # Resultado final
    print('\n' + '=' * 60)
    print('📊 RESULTADO FINAL:')
    print(f'   ✅ Testes passaram: {test_passed}/{test_total}')
    print(f'   🎯 Taxa de sucesso: {(test_passed/test_total)*100:.1f}%')
    
    if test_passed == test_total:
        print('\n🎉 SUCESSO: Sistema de verificação funcionando corretamente!')
        print('🚀 Fix aplicado com sucesso - novos escaladores podem se verificar')
        return True
    else:
        print(f'\n⚠️ ATENÇÃO: {test_total - test_passed} teste(s) falharam')
        print('🚨 Verificar logs e aplicar correções adicionais se necessário')
        return False

if __name__ == '__main__':
    success = test_verification_system()
    sys.exit(0 if success else 1)