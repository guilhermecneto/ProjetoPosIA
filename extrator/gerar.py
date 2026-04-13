from PIL import Image, ImageDraw
import os

os.makedirs("../documentos_medicos", exist_ok=True)

def criar_atestado(nome_paciente, crm, dias, cid, arquivo):
    # Cria uma imagem em branco
    img = Image.new('RGB', (800, 600), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    
    texto = f"""
    HOSPITAL CENTRAL DA CIDADE
    ATENDIMENTO EM EMERGENCIA
    ========================================================
    
    A T E S T A D O   M E D I C O
    ========================================================
    
    Atesto para os devidos fins que o paciente:
    {nome_paciente}
    
    Foi atendido(a) na data de 27 de Marco de 2026.
    Apresenta quadro clinico incompativel com trabalho.
    
    Concedo {dias} dias de repouso medico obrigatorio
    a partir desta data.
    
    CID-10: {cid}
    
    ========================================================
    
    Julio Cesar Batista
    CRM - {crm}
    (Assinatura Ilegivel)
    """
    
    # Texto em preto sem custom font só para simular documento escaneado/legível
    d.text((50, 50), texto, fill=(0, 0, 0))
    img.save(f"../documentos_medicos/{arquivo}")

import random

# Gerar apenas 3 atestados conforme solicitado
criar_atestado("Pedro de Alcântara", "55443/SP", 4, "A09", "atestado_pedro.png")
criar_atestado("Renata Vasconcelos", "12399/RJ", 2, "J01", "atestado_renata.png")
criar_atestado("Guilherme", "11223/SP", 5, "M54", "atestado_guilherme.png")

print("Os 3 atestados foram gerados com sucesso!")
