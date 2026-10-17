import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql_fix_leitura = """
CREATE OR REPLACE FUNCTION conexo_executar_leitura(query_str text)
RETURNS json LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  ret json;
  clean_q text;
BEGIN
  clean_q := TRIM(query_str);
  
  -- Remove trailing semicolon if present
  IF clean_q LIKE '%;' THEN
    clean_q := RTRIM(clean_q, ';');
  END IF;
  
  -- Bloqueio de escrita usando regex com limites de palavras (evita bloquear 'created_at')
  IF LOWER(clean_q) ~* '\\m(insert|update|delete|drop|alter|truncate|grant|create\\s+table|create\\s+function|create\\s+index|create\\s+view|create\\s+or\\s+replace)\\M' THEN
    RAISE EXCEPTION 'Apenas consultas de leitura (SELECT) são permitidas.';
  END IF;
  
  EXECUTE 'SELECT json_agg(t) FROM (' || clean_q || ') t' INTO ret;
  RETURN COALESCE(ret, '[]'::json);
END;
$$;
"""

res = supabase.rpc("exec_sql", {"query": sql_fix_leitura}).execute()
print("conexo_executar_leitura updated in Supabase:", res.data)
