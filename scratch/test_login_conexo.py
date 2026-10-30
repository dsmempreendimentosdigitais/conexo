import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get("SUPABASE_URL")

# Busca a anon key no .env ou no nexo-pwa/.env
anon_key = os.environ.get("VITE_SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY")
if not anon_key and os.path.exists("nexo-pwa/.env"):
    for line in open("nexo-pwa/.env"):
        if "VITE_SUPABASE_ANON_KEY" in line:
            anon_key = line.split("=")[1].strip().strip("\"'")

print("Anon Key found:", bool(anon_key))
sb = create_client(url, anon_key)
res = sb.auth.sign_in_with_password({"email": "conexo.dev.ai@gmail.com", "password": "S@muca88"})
print(f"Login OK! User ID: {res.user.id} | Email: {res.user.email}")
