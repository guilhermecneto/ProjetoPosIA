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

criar_atestado("Pedro de Alcântara", "55443/SP", 4, "A09", "atestado_pedro.png")
criar_atestado("Renata Vasconcelos", "12399/RJ", 2, "J01", "atestado_renata.png")

nomes = ["Guilherme", "Carlos Silva", "Mariana Souza", "Roberto Alves", "Ana Maria", "Joao Paulo", "Fernanda Costa", "Lucas Lima", "Paulo Mendes", "Rita Carvalho"]
crms = ["11223/SP", "33445/RJ", "55667/MG", "77889/PR", "99001/SC"]
# Adicionando alguns CIDs estratégicos para avaliarmos o Macro (Ergonomia, Psicológico e Comuns)
casos = [
    ("M54", 5), # Dorsalgia (Dores nas costas)
    ("M65", 7), # Tenossinovite
    ("M54", 4), # Dorsalgia
    ("F41", 10), # Ansiedade
    ("Z73", 15), # Esgotamento (Burnout)
    ("J11", 3), # Influenza (Gripe)
    ("A09", 2), # Gastroenterite
    ("H10", 3), # Conjuntivite
    ("U07.1", 5), # COVID
    ("U07.1", 7)  # COVID
]

for i, nome in enumerate(nomes):
    crm = random.choice(crms)
    cid, dias = casos[i]
    criar_atestado(nome, crm, dias, cid, f"atestado_{nome.split()[0].lower()}_{i}.png")

print("Os 10 novos atestados aleatórios foram gerados com sucesso!")
