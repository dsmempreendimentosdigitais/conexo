import sys, os, json

with open("scratch/top50_clientes_analisados.json", "r", encoding="utf-8") as f:
    clientes = json.load(f)

total_fat = sum(c["faturamento_total"] for c in clientes)
total_met = sum(c["metros_total"] for c in clientes)
total_ped = sum(c["total_pedidos"] for c in clientes)

linhas = []
linhas.append("=" * 110)
linhas.append("          DESIGNTEX TECIDOS — MAPEAMENTO ESTRATÉGICO DOS 50 MELHORES CLIENTES")
linhas.append("              (PERFIL DE CONSUMO, DNA DE TECIDOS E RECOMENDAÇÕES DA DEISE)")
linhas.append("=" * 110)
linhas.append("")
linhas.append("RESUMO EXECUTIVO DA CARTEIRA TOP 50:")
linhas.append(f"• Total de Clientes Analisados: 50 maiores compradores históricos")
linhas.append(f"• Faturamento Acumulado Top 50: R$ {total_fat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
linhas.append(f"• Metragem Total Faturada:      {total_met:,.1f} metros".replace(",", "X").replace(".", ",").replace("X", "."))
linhas.append(f"• Volume Total de Pedidos:      {total_ped:,} pedidos".replace(",", "."))
linhas.append(f"• Ticket Médio Geral da Base:   R$ {total_fat/total_ped:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
linhas.append("")
linhas.append("-" * 110)
linhas.append("RANKING DETALHADO DOS 50 MELHORES CLIENTES")
linhas.append("-" * 110)

for c in clientes:
    pos = c["posicao"]
    nome = c["nome"]
    cod = c["codigo"]
    rep = c["representante"]
    fat = f"R$ {c['faturamento_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    met = f"{c['metros_total']:,.1f} m".replace(",", "X").replace(".", ",").replace("X", ".")
    ped = c["total_pedidos"]
    tm = f"R$ {c['ticket_medio']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    pm = f"R$ {c['preco_medio_m']:,.2f}/m".replace(",", "X").replace(".", ",").replace("X", ".")
    ult = c["ultimo_pedido"]
    
    artigos_str = " | ".join(c["top_artigos"][:2]) if c["top_artigos"] else "Itens diversos"
    cores_str = ", ".join(c["top_cores"][:3]) if c["top_cores"] else "Cores diversas"
    bases_str = ", ".join(c["bases_compradas"]) if c["bases_compradas"] else "Geral"
    rec = c["recomendacao_deise"]

    linhas.append(f"#{pos:02d}. {nome} (Código: {cod})")
    linhas.append(f"     👤 Representante: {rep}")
    linhas.append(f"     💰 Faturamento: {fat} | 📏 Metragem: {met} | 📦 Pedidos: {ped} | 🎟️ Ticket Médio: {tm}")
    linhas.append(f"     📅 Último Pedido Registrado: {ult} | Preço Médio Praticado: {pm}")
    linhas.append(f"     🧵 Bases Preferidas: {bases_str}")
    linhas.append(f"     ⭐ Principais Artigos Comprados: {artigos_str}")
    linhas.append(f"     🎨 Cores Mais Recorrentes: {cores_str}")
    linhas.append(f"     🎯 Oportunidade Ativa Deise: {rec}")
    linhas.append("." * 110)

linhas.append("")
linhas.append("=" * 110)
linhas.append("           Designtex Tecidos — Inteligência Comercial CONEXO / DEISE")
linhas.append("=" * 110)

conteudo = "\n".join(linhas)

out_file = "MAPEAMENTO_TOP_50_CLIENTES_DESIGNTEX.txt"
with open(out_file, "w", encoding="utf-8") as f:
    f.write(conteudo)

print(f"Relatório formatado gerado em {out_file} com {len(linhas)} linhas!")
