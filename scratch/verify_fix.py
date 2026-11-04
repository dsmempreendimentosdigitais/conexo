import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Let's test updating the ticket from the screenshot!
# The ticket in the screenshot is:
# Cliente: SHIRLEY MARTINS LTDA (4863)
# Pedido/OP: 36481
# Nota Fiscal: NF 75098
# Let's find this ticket:
res = sb.table("sac_tickets").select("id, ticket_number, status, op, dados_cliente").eq("op", "36481").execute()
print("Ticket 36481:", res.data)

if res.data:
    ticket_id = res.data[0]["id"]
    current_status = res.data[0]["status"]
    print(f"Current status of ticket {ticket_id}: {current_status}")
    
    # Try updating to 'Disposição'
    try:
        up_res = sb.table("sac_tickets").update({"status": "Disposição"}).eq("id", ticket_id).execute()
        print("Successfully updated status to 'Disposição':", up_res.data[0]["status"])
        
        # Restore back to original status so user can test the UI himself!
        sb.table("sac_tickets").update({"status": current_status}).eq("id", ticket_id).execute()
        print("Restored back to original status:", current_status)
    except Exception as e:
        print("Failed to update status to Disposição:", e)
