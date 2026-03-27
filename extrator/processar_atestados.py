import os
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT
import glob

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da API do Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("ERRO CRÍTICO: A variável de ambiente GEMINI_API_KEY não foi encontrada.")
    print("Crie um arquivo .env na pasta extrator/ contendo: GEMINI_API_KEY=sua_chave_aqui")
    exit(1)

genai.configure(api_key=API_KEY)

# Configurar o modelo gemini-1.5-flash
generation_config = {
    "temperature": 0.1,  # Temperatura baixa para maior fidelidade aos fatos
    "response_mime_type": "application/json",
}

try:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config=generation_config
    )
except Exception as e:
    print(f"Erro ao instanciar modelo: {e}. Atualize a biblioteca google-generativeai.")
    exit(1)

PASTA_DOCUMENTOS = "../documentos_medicos"
ARQUIVO_DADOS = "../frontend/public/dados_extraidos.json"

def init_json():
    os.makedirs(os.path.dirname(ARQUIVO_DADOS), exist_ok=True)
    if not os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
            json.dump([], f)

def carregar_dados():
    try:
        with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def enviar_para_gemini(caminho_arquivo):
    print(f"--- Processando arquivo: {os.path.basename(caminho_arquivo)}")
    try:
        # Fazer upload do arquivo para o Google Gemini API
        print("Enviando arquivo para a nuvem do Gemini API...")
        arquivo_upload = genai.upload_file(caminho_arquivo)
        
        # Gera o conteúdo
        prompt_solicitacao = "Extraia as informações deste atestado e retorne como JSON restrito."
        print("Analisando atestado com inteligência artificial...")
        response = model.generate_content([arquivo_upload, prompt_solicitacao])
        
        # Apagar o arquivo na nuvem após uso para evitar acúmulo e privacidade
        genai.delete_file(arquivo_upload.name)
        
        resultado_json = response.text.strip()
        
        # Corrige retorno do modelo caso venha com markdown
        if resultado_json.startswith("```json"):
            resultado_json = resultado_json.replace("```json\n", "").replace("```json", "").replace("\n```", "").replace("```", "")
            
        dados = json.loads(resultado_json)
        # Adiciona no JSON a referência de qual foi o arquivo processado
        dados['arquivo_origem'] = os.path.basename(caminho_arquivo)
        return dados
    except Exception as e:
        print(f"Erro ao processar {caminho_arquivo}: {e}")
        return None

def main():
    init_json()
    dados_atuais = carregar_dados()
    arquivos_ja_processados = [d.get('arquivo_origem') for d in dados_atuais]
    
    # Busca arquivos suportados na pasta
    tipos_suportados = ('*.png', '*.jpg', '*.jpeg', '*.pdf', '*.webp')
    arquivos_para_processar = []
    
    for ext in tipos_suportados:
        arquivos_para_processar.extend(glob.glob(os.path.join(PASTA_DOCUMENTOS, ext)))
        arquivos_para_processar.extend(glob.glob(os.path.join(PASTA_DOCUMENTOS, ext.upper())))
    
    novos_dados = []
    for arquivo in arquivos_para_processar:
        nome_arquivo = os.path.basename(arquivo)
        if nome_arquivo not in arquivos_ja_processados:
            resultado = enviar_para_gemini(arquivo)
            if resultado:
                novos_dados.append(resultado)
                print(f"SUCESSO: {nome_arquivo} processado!")
                time.sleep(2)  # Delay simples para evitar bater no rate limit da API
                
    if novos_dados:
        dados_atuais.extend(novos_dados)
        salvar_dados(dados_atuais)
        print(f"\n[{len(novos_dados)}] novos atestados processados e salvos em: {ARQUIVO_DADOS}")
    else:
        print("\nNenhum atestado MÈDICO novo encontrado para processar.")

if __name__ == "__main__":
    main()
