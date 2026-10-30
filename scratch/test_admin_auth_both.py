import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
from supabase import create_client
from admin_router import require_admin
import requests

load_dotenv()
url = os.environ.get("SUPABASE_URL")
anon_key = os.environ.get("VITE_SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY")
if not anon_key and os.path.exists("nexo-pwa/.env"):
    for line in open("nexo-pwa/.env"):
        if "VITE_SUPABASE_ANON_KEY" in line:
            anon_key = line.split("=")[1].strip().strip("\"'")

sb = create_client(url, anon_key)

# Testa login de samuel.mc85@gmail.com ou conexo.dev.ai@gmail.com
for email, pwd in [("conexo.dev.ai@gmail.com", "S@muca88")]:
    try:
        res = sb.auth.sign_in_with_password({"email": email, "password": pwd})
        token = res.session.access_token
        print(f"\nTestando token de {email}...")
        try:
            admin_data = require_admin(authorization=f"Bearer {token}")
            print(f"require_admin SUCESSO: {admin_data}")
        except Exception as e:
            print(f"require_admin ERRO: {e}")
    except Exception as e:
        print(f"Erro login {email}: {e}")
