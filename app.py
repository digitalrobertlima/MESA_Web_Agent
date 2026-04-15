import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from ollama import AsyncClient
from duckduckgo_search import DDGS
from dotenv import load_dotenv

# Tenta importar as configurações. Se não existir, usa um prompt padrão.
try:
    from config.settings import SYSTEM_PROMPT
except ImportError:
    SYSTEM_PROMPT = "Você é o assistente estratégico do Prof. Robert Lima."

load_dotenv()
app = FastAPI()

# Permite que seu site na Vercel fale com este código no Hugging Face
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clientes de Nuvem
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
cloud_client = AsyncClient(
    host='https://api.ollama.com',
    headers={'Authorization': f'Bearer {os.getenv("OLLAMA_API_KEY")}'}
)

def pesquisar_web(termo):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(termo, max_results=3)]
            return "\n".join([f"{r['title']}: {r['body']}" for r in results])
    except:
        return ""

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_text = data.get("message")
    
    # 1. Pesquisa Web Automática
    contexto_web = ""
    if "?" in user_text or any(w in user_text.lower() for w in ['como', 'onde', 'qual']):
        contexto_web = f"\n\n[DADOS WEB]:\n{pesquisar_web(user_text)}"

    # 2. Resposta da IA (M.E.S.A. Persona)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + contexto_web},
        {"role": "user", "content": user_text}
    ]
    
    response = await cloud_client.chat(model=os.getenv("OLLAMA_MODEL"), messages=messages)
    reply = response['message']['content']

    # 3. Registro Estratégico no Supabase
    # Detecta se há um número (potencial lead) e salva no banco de dados
    if any(c.isdigit() for c in user_text) and len(user_text) >= 8:
        try:
            supabase.table("leads").insert({
                "whatsapp": user_text, 
                "interesse": "Interessado via Web"
            }).execute()
        except:
            pass

    return {"response": reply}

if __name__ == "__main__":
    import uvicorn
    # A porta 7860 é OBRIGATÓRIA para o Hugging Face Spaces
    uvicorn.run(app, host="0.0.0.0", port=7860)