import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from ollama import AsyncClient
from duckduckgo_search import DDGS
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Permite que seu site na Vercel fale com este motor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialização segura dos clientes
try:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
    
    cloud_client = AsyncClient(
        host='https://api.ollama.com',
        headers={'Authorization': f'Bearer {os.getenv("OLLAMA_API_KEY")}'}
    )
except Exception as e:
    print(f"Erro na inicialização dos serviços: {e}")

def pesquisar_web(termo):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(termo, max_results=3)]
            return "\n".join([f"{r['title']}: {r['body']}" for r in results])
    except:
        return "Serviço de busca temporariamente indisponível."

@app.get("/")
async def root():
    return {"status": "M.E.S.A. v4.5 Online", "local": "Hugging Face Cloud"}

@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        user_text = data.get("message", "")
        
        # Lógica de Busca
        contexto_web = ""
        termos = ['como', 'onde', 'qual', '?', 'ajuda', 'erro']
        if any(t in user_text.lower() for t in termos):
            dados = pesquisar_web(user_text)
            contexto_web = f"\n\n[DADOS WEB RECENTES]:\n{dados}"

        # Persona do Professor Robert
        prompt_base = "Você é o assistente estratégico do Prof. Robert Lima. Use um tom sofisticado e industrial organic. Se houver dados web, use-os."
        
        messages = [
            {"role": "system", "content": prompt_base + contexto_web},
            {"role": "user", "content": user_text}
        ]
        
        response = await cloud_client.chat(model=os.getenv("OLLAMA_MODEL", "glm-4.7:cloud"), messages=messages)
        reply = response['message']['content']

        # Registro no Supabase (se o telefone aparecer)
        if supabase and any(c.isdigit() for c in user_text) and len(user_text) >= 8:
            supabase.table("leads").insert({"whatsapp": user_text, "interesse": "Web Lead"}).execute()

        return {"response": reply}
    except Exception as e:
        return {"response": f"O assistente encontrou um soluço técnico: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    # A porta 7860 é fundamental para o Hugging Face
    uvicorn.run(app, host="0.0.0.0", port=7860)