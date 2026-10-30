import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

supabase.table("conexo_usuarios").update({
    "perfil": "admin",
    "nome": "Samuel (Master Admin)",
    "setor": "Diretoria Executiva"
}).eq("email", "samuel.mc85@gmail.com").execute()

print("User updated to admin!")
