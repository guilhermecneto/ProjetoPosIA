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

    time.sleep(15) # Respeitar rate limit

    # 4. FILTRO DE PRIVACIDADE E LGPD (ANONIMIZAÇÃO)
    skill_privacidade = carregar_skill("FiltroPrivacidadeLGPD.md")
    model_privacidade = genai.GenerativeModel("gemini-flash-latest", system_instruction=skill_privacidade)
    print("[4/5] Aplicando filtro de sanitização LGPD e Sigilo Médico...")
    try:
        res_lgpd = model_privacidade.generate_content(f"Revise e anonimize este JSON removendo dados de diagnóstico: {json.dumps(dados)}")
        lgpd_json = json.loads(res_lgpd.text.strip().replace("```json", "").replace("```", ""))
        dados['privacidade_lgpd'] = lgpd_json
    except Exception as e:
        print(f"Erro na anonimização LGPD: {e}")
        dados['privacidade_lgpd'] = {"sucesso_anonimizacao": False, "parecer_dpo": "Falha ao aplicar filtro de privacidade."}

    time.sleep(15) # Respeitar rate limit

    # 5. PLANEJADOR DE RETORNO AO TRABALHO (ONBOARDING & PRODUTIVIDADE)
    skill_retorno = carregar_skill("PlanejadorRetornoTrabalho.md")
    model_retorno = genai.GenerativeModel("gemini-flash-latest", system_instruction=skill_retorno)
    print("[5/5] Gerando plano corporativo de readaptação (RH/Onboarding)...")
    try:
        # Pega a quantidade original de dias extraídas para basear a diretriz (tenta do LGPD primeiro, senão dados brutos)
        qtd_dias = dados.get("privacidade_lgpd", {}).get("dados_seguros_para_rh", {}).get("dias_afastamento") 
        if not qtd_dias:
            qtd_dias = dados.get("dias", "Não especificado")
        payload_retorno = {"dias_afastamento_estimados": qtd_dias}
        
        # Envia apenas {"dias"} para blindar e garantir que o modelo não acesse nem leia nomes de doenças ou CID
        res_retorno = model_retorno.generate_content(f"Com base apenas neste tempo de afastamento, gere as diretrizes de RH: {json.dumps(payload_retorno)}")
        retorno_json = json.loads(res_retorno.text.strip().replace("```json", "").replace("```", ""))
        dados['plano_de_retorno_rh'] = retorno_json
    except Exception as e:
        print(f"Erro na geração de diretrizes de retorno: {e}")
        dados['plano_de_retorno_rh'] = {"plano_retorno_gerado": False, "orientacao_ergonomica_padrao": "Bem-vindo de volta! Faça pausas e ajuste sua cadeira."}

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

    # 6. ANÁLISE MACRO: SAÚDE OCUPACIONAL E PREVENÇÃO DE RISCO NO AMBIENTE
    if dados_atuais:
        print("\n--- Analisando o Cenário Geral de Saúde Ocupacional (Macro) ---")
        skill_macro = carregar_skill("AnalistaSaudeOcupacional.md")
        if skill_macro:
            model_macro = genai.GenerativeModel("gemini-flash-latest", system_instruction=skill_macro)
            
            # Extraímos do banco apenas o panorama da doença e dias associados (sem nomes, sem atestado bruto)
            amostra_historico = [{"doenca_cid": d.get("cid", d.get("diagnostico", "Não identificado")), "dias": d.get("dias", 1)} for d in dados_atuais]
                
            try:
                res_macro = model_macro.generate_content(f"Gere o relatório de Saúde Ocupacional baseado nesta amostragem corporativa (evite usar CIDs explicitamente na resposta, foque no motivo e solução): {json.dumps(amostra_historico)}")
                relatorio_json = json.loads(res_macro.text.strip().replace("```json", "").replace("```", ""))
                
                # Salva o relatório num JSON separado para o painel de diretoria/RH
                caminho_relatorio = "../frontend/public/relatorio_ocupacional.json"
                os.makedirs(os.path.dirname(caminho_relatorio), exist_ok=True)
                with open(caminho_relatorio, 'w', encoding='utf-8') as f:
                    json.dump(relatorio_json, f, indent=4, ensure_ascii=False)
                print("Relatório Corporativo de Risco Ocupacional gerado em: " + caminho_relatorio)
            except Exception as e:
                print(f"Erro na geração do relatório ocupacional macro: {e}")

if __name__ == "__main__":
    main()
