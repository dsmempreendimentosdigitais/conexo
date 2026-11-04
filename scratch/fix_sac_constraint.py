import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Let's inspect all tables or check exec_sql definition
try:
    # Let's try to update the constraint or drop and re-add it!
    # First, let's see what happens if we try to insert or update a test status
    sql = """
    ALTER TABLE public.sac_tickets DROP CONSTRAINT IF EXISTS sac_tickets_status_check;
    ALTER TABLE public.sac_tickets ADD CONSTRAINT sac_tickets_status_check 
    CHECK (status IN ('Aberto', 'Em Análise', 'Respondido', 'Concluído', 'Disposição', 'Aguardando NF de Devolução', 'Aguardando Coleta'));
    """
    res = sb.rpc("exec_sql", {"query": sql}).execute()
    print("Result of altering constraint:", res.data)
except Exception as e:
    print("Error:", e)
