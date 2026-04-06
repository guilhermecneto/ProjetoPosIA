import os
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
import glob
import re

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da API do Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("ERRO CRÍTICO: A variável de ambiente GEMINI_API_KEY não foi encontrada.")
    exit(1)

genai.configure(api_key=API_KEY)

PASTA_DOCUMENTOS = "../documentos_medicos"
ARQUIVO_DADOS = "../frontend/public/dados_extraidos.json"
PASTA_SKILLS = "../skills"

def carregar_skill(nome_arquivo):
    caminho = os.path.join(PASTA_SKILLS, nome_arquivo)
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            # Remove o frontmatter YAML (entre --- e ---)
            conteudo_puro = re.sub(r'---.*?---', '', conteudo, flags=re.DOTALL).strip()
            return conteudo_puro
    except Exception as e:
        print(f"Erro ao carregar skill {nome_arquivo}: {e}")
        return None

def init_json():
    os.makedirs(os.path.dirname(ARQUIVO_DADOS), exist_ok=True)
    if not os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
            json.dump([], f)

def carregar_dados_existentes():
    try:
        with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def processar_atestado_completo(caminho_arquivo):
    print(f"\n--- Iniciando Pipeline: {os.path.basename(caminho_arquivo)} ---")
    
    # 1. EXTRAÇÃO
    skill_extracao = carregar_skill("SalvarDadosAtestados.md")
    model_extrator = genai.GenerativeModel("gemini-flash-latest", system_instruction=skill_extracao)
    
    try:
        arquivo_upload = genai.upload_file(caminho_arquivo)
        print("[1/3] Extraindo dados do documento...")
        response = model_extrator.generate_content([arquivo_upload, "Extraia os dados conforme instruído."])
        genai.delete_file(arquivo_upload.name)
        
        dados = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        dados['arquivo_origem'] = os.path.basename(caminho_arquivo)
    except Exception as e:
        print(f"Erro na extração: {e}")
        return None

    time.sleep(15) # Respeitar rate limit

    # 2. AUDITORIA
    skill_auditoria = carregar_skill("AuditorAtestado.md")
    model_auditor = genai.GenerativeModel("gemini-flash-latest", system_instruction=skill_auditoria)
    print("[2/3] Realizando auditoria de consistência...")
    try:
        res_audit = model_auditor.generate_content(f"Analise estes dados e retorne o JSON de auditoria: {json.dumps(dados)}")
        auditoria_json = json.loads(res_audit.text.strip().replace("```json", "").replace("```", ""))
        dados['auditoria'] = auditoria_json
    except Exception as e:
        print(f"Erro na auditoria: {e}")
        dados['auditoria'] = {"status": "Erro", "alertas": ["Falha no processamento da auditoria"]}

    time.sleep(15) # Respeitar rate limit

    # 3. VALIDAÇÃO DE CRM E ESPECIALIDADE
    skill_validacao = carregar_skill("ValidacaoEspecialidadeCRM.md")
    model_validador = genai.GenerativeModel("gemini-flash-latest", system_instruction=skill_validacao)
    print("[3/3] Validando CRM e Especialidade...")
    try:
        res_val = model_validador.generate_content(f"Analise o CRM e a Especialidade deste JSON: {json.dumps(dados)}")
        validacao_json = json.loads(res_val.text.strip().replace("```json", "").replace("```", ""))
        dados['validacao_profissional'] = validacao_json
    except Exception as e:
        print(f"Erro na validação profissional: {e}")
        dados['validacao_profissional'] = {"crm_formato_valido": False, "conclusao_tecnica": "Falha na validação"}

    return dados

def main():
    init_json()
    dados_atuais = carregar_dados_existentes()
    arquivos_ja_processados = [d.get('arquivo_origem') for d in dados_atuais]
    
    tipos_suportados = ('*.png', '*.jpg', '*.jpeg', '*.pdf', '*.webp')
    arquivos = []
    for ext in tipos_suportados:
        arquivos.extend(glob.glob(os.path.join(PASTA_DOCUMENTOS, ext)))
    
    novos_dados = []
    for arquivo in arquivos:
        if os.path.basename(arquivo) not in arquivos_ja_processados:
            resultado = processar_atestado_completo(arquivo)
            if resultado:
                novos_dados.append(resultado)
                time.sleep(2) # Rate limit safety entre arquivos
                
    if novos_dados:
        dados_atuais.extend(novos_dados)
        salvar_dados(dados_atuais)
        print(f"\nFinalizado! {len(novos_dados)} novos atestados processados.")
    else:
        print("\nNenhum novo atestado para processar.")

if __name__ == "__main__":
    main()
