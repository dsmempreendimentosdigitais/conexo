import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]
    SUPABASE_URL     = os.environ["SUPABASE_URL"]
    SUPABASE_KEY     = os.environ["SUPABASE_SERVICE_KEY"]  # service_role (backend)
    
    # Detecção automática de chave Gemini para usar a API de compatibilidade da Google
    IS_GEMINI        = OPENAI_API_KEY.startswith("AIzaSy")
    OPENAI_BASE_URL  = "https://generativelanguage.googleapis.com/v1beta/openai/" if IS_GEMINI else None
    
    MODEL_ROUTER     = "gemini-1.5-flash" if IS_GEMINI else "gpt-4o-mini"
    MODEL_FORMATTER  = "gemini-1.5-flash" if IS_GEMINI else "gpt-4o"

    EMPRESA          = "Designtex Tecidos"
    TIMEZONE         = "America/Sao_Paulo"

    # Chave de admin (só você tem — protege os endpoints de onboarding)
    ADMIN_KEY        = os.environ["CONEXO_ADMIN_KEY"]

    # Tavily — web search para inteligência de mercado (fase 2)
    TAVILY_API_KEY   = os.environ.get("TAVILY_API_KEY", "")

config = Config()
