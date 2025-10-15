#!/usr/bin/env python3
from utils import create_offline_image

if __name__ == "__main__":
    print("Gerando imagem offline...")
    success, result = create_offline_image()
    
    if success:
        print(f"✅ Imagem gerada: {result}")
    else:
        print(f"❌ Erro: {result}")