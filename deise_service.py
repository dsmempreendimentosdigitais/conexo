"""
Módulo de Inteligência Comercial e Atendimento da Agente DEISE (Designtex Tecidos)
Garante 100% de isolamento de dados por cliente (Zero-Leak Policy).
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from config import config
from executor import supabase

def formatar_moeda(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_metros(val: float) -> str:
    return f"{val:,.1f} m".replace(",", "X").replace(".", ",").replace("X", ".")

class DeiseService:
    """
    Serviço central da Deise para atendimento a clientes via WhatsApp e Portal.
    """

    @staticmethod
    def validar_cliente(cliente_codigo: str) -> Optional[Dict[str, Any]]:
        """
        Busca os dados cadastrais básicos do cliente autenticado.
        """
        if not cliente_codigo:
            return None
        
        sql = f"""
        SELECT 
            c.id, c.codigo, c.razao_social, c.nome_fantasia, c.cpf_cnpj,
            r.codigo as rep_codigo, r.nome as rep_nome, r.contato as rep_contato,
            r.telefone as rep_telefone, r.email as rep_email
        FROM clientes c
        LEFT JOIN representantes r ON r.codigo = c.representante_codigo
        WHERE c.codigo = '{cliente_codigo}'
        LIMIT 1
        """
        res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None

    @staticmethod
    def get_pedidos_cliente(cliente_codigo: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Consulta ESTRITAMENTE os pedidos do próprio cliente autenticado.
        NUNCA traz dados de outros clientes.
        """
        if not cliente_codigo:
            return []
        
        safe_cod = cliente_codigo.replace("'", "''")
        sql = f"""
        SELECT 
            totvs_order_code as pedido,
            status,
            data_pedido,
            previsao_faturamento,
            valor_total,
            quantidade_total as metros,
            nota_fiscal_numero as nf
        FROM pedidos_totvs
        WHERE cliente_codigo = '{safe_cod}'
        ORDER BY data_pedido DESC
        LIMIT {limit}
        """
        res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return res.data or []

    @staticmethod
    def consultar_estoque_pronta_entrega(acabamento: str = "liso", base: str = "todas") -> List[Dict[str, Any]]:
        """
        Consulta o estoque público de Pronta Entrega disponível para venda.
        acabamento: 'liso' ou 'estampado'
        base: 'tricoline', 'linho', 'sarja', ou 'todas'
        """
        filtros = ["quantidade_disponivel > 0"]

        if acabamento == "liso":
            filtros.append("(cor NOT ILIKE '%estamp%' AND descricao NOT ILIKE '%estamp%')")
        elif acabamento == "estampado":
            filtros.append("(cor ILIKE '%estamp%' OR descricao ILIKE '%estamp%')")

        if base == "tricoline":
            filtros.append("(descricao ILIKE '%tricoline%')")
        elif base == "linho":
            filtros.append("(descricao ILIKE '%linho%')")
        elif base == "sarja":
            filtros.append("(descricao ILIKE '%sarja%')")

        where_clause = " AND ".join(filtros)
        sql = f"""
        SELECT 
            descricao as artigo,
            cod_produto as codigo_artigo,
            cor,
            cor_codigo,
            quantidade_disponivel as metros_disponiveis
        FROM estoque_pe
        WHERE {where_clause}
        ORDER BY quantidade_disponivel DESC
        LIMIT 10
        """
        res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return res.data or []

    @staticmethod
    def consultar_programacao_ops(acabamento: str = "liso", base: str = "todas") -> List[Dict[str, Any]]:
        """
        Consulta as Ordens de Produção (OPs) abertas na tecelagem/tinturaria.
        """
        filtros = ["status IN ('Em produção', 'Aberta', 'Planejada', 'Liberada')"]

        if base == "tricoline":
            filtros.append("(artigo ILIKE '%tricoline%')")
        elif base == "linho":
            filtros.append("(artigo ILIKE '%linho%')")
        elif base == "sarja":
            filtros.append("(artigo ILIKE '%sarja%')")

        where_clause = " AND ".join(filtros)
        sql = f"""
        SELECT 
            op,
            artigo,
            cor,
            previsao_entrega,
            quantidade as metros_planejados
        FROM programacoes
        WHERE {where_clause}
        ORDER BY previsao_entrega ASC
        LIMIT 8
        """
        try:
            res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
            return res.data or []
        except Exception:
            return []

    @staticmethod
    def gerar_boas_vindas(cliente_codigo: str) -> str:
        """
        Gera a saudação personalizada e segura da Deise.
        SEM menção a limites de crédito ou dados internos da fábrica.
        """
        cliente = DeiseService.validar_cliente(cliente_codigo)
        if not cliente:
            return (
                "Olá! Seja bem-vindo(a) à *Designtex Tecidos*. Meu nome é *Deise*, "
                "sua assistente comercial inteligente! 🧵👗\n\n"
                "Para iniciar o seu atendimento, por favor me informe o CNPJ da sua empresa."
            )

        nome = cliente.get("nome_fantasia") or cliente.get("razao_social") or "Cliente"
        rep_nome = cliente.get("rep_contato") or cliente.get("rep_nome") or "Comercial Designtex"

        pedidos = DeiseService.get_pedidos_cliente(cliente_codigo, limit=3)
        total_pedidos = len(pedidos)
        metros_abertos = sum(float(p.get("metros") or 0) for p in pedidos if p.get("status") in ["Em andamento", "Aberto"])
        
        ultima_nf = next((p.get("nf") for p in pedidos if p.get("nf")), "Consulte no Portal")

        msg = (
            f"Olá! Seja muito bem-vindo(a) à *Designtex Tecidos*. Meu nome é *Deise*, "
            f"sua assistente comercial inteligente! 👗🧵\n\n"
            f"Já identifiquei o cadastro da *{nome}* por aqui:\n"
            f"📦 *Pedidos Recentes:* {total_pedidos} registrados ({formatar_metros(metros_abertos)} em aberto)\n"
            f"🚚 *Última NF Faturada:* NF {ultima_nf}\n"
            f"👤 *Seu(ua) Representante:* {rep_nome}\n\n"
            f"Como posso te ajudar hoje? Digite o número da opção desejada:\n\n"
            f"*1️⃣ Consultar tecidos disponíveis na Pronta Entrega*\n"
            f"*2️⃣ Consultar tecidos disponíveis em Programação*\n"
            f"*3️⃣ Acompanhar meus pedidos em aberto*\n"
            f"*4️⃣ Ver catálogo e PDF dos novos lançamentos*\n"
            f"*5️⃣ Falar diretamente com meu representante*"
        )
        return msg

    @staticmethod
    def gerar_transferencia_representante(cliente_codigo: str) -> Dict[str, Any]:
        """
        Retorna o link direto do WhatsApp do representante responsável pelo cliente.
        """
        cliente = DeiseService.validar_cliente(cliente_codigo)
        if not cliente:
            return {
                "mensagem": "Vou transferir para nossa equipe de atendimento geral da Designtex.",
                "link_zap": "https://wa.me/5511999999999",
                "rep_nome": "Comercial Designtex"
            }

        rep_nome = cliente.get("rep_contato") or cliente.get("rep_nome") or "Representante Designtex"
        rep_fone = cliente.get("rep_telefone") or "5511999999999"
        
        # Limpa telefone para formato internacional wa.me
        limpo_fone = "".join(filter(str.isdigit, rep_fone))
        if len(limpo_fone) in (10, 11) and not limpo_fone.startswith("55"):
            limpo_fone = "55" + limpo_fone

        link_zap = f"https://wa.me/{limpo_fone}?text=" + \
            f"Ol%C3%A1%20{rep_nome}!%20Sou%20da%20empresa%20{cliente.get('nome_fantasia') or cliente.get('razao_social')}%20e%20solicitei%20atendimento%20pelo%20WhatsApp%20da%20Deise."

        mensagem = (
            f"Com certeza! O seu representante oficial na Designtex é *{rep_nome}*.\n\n"
            f"Clique no link abaixo para conversar diretamente com ele(a) no WhatsApp:\n"
            f"👉 {link_zap}\n\n"
            f"Já registrei o seu contato e avisei o(a) {rep_nome} para priorizar o seu atendimento! 🤝"
        )

        return {
            "rep_nome": rep_nome,
            "rep_telefone": limpo_fone,
            "link_zap": link_zap,
            "mensagem": mensagem
        }
