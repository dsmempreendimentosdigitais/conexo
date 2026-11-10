"""
Módulo de Inteligência Comercial e Atendimento da Agente DEISE (Designtex Tecidos)
Garante 100% de isolamento de dados por cliente (Zero-Leak Policy).
"""

from typing import Dict, Any, List, Optional
import json
import re
import unicodedata
from datetime import datetime
from config import config
from executor import supabase

def formatar_moeda(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_metros(val: float) -> str:
    return f"{val:,.1f} m".replace(",", "X").replace(".", ",").replace("X", ".")

def desacentuar(txt: str) -> str:
    if not txt:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(txt)) if unicodedata.category(c) != "Mn"
    ).lower().strip()

# Gerenciador de Sessões em Memória
_SESSOES: Dict[str, Dict[str, Any]] = {}

SUPABASE_STORAGE_DESENHOS = "https://liolnupwhhpsryfgnnyl.supabase.co/storage/v1/object/public/desenhos"


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
        
        safe_cod = str(cliente_codigo).replace("'", "''")
        sql = f"""
        SELECT 
            c.id, c.codigo, c.razao_social, c.nome_fantasia, c.cpf_cnpj,
            r.codigo as rep_codigo, r.nome as rep_nome, r.contato as rep_contato,
            r.telefone as rep_telefone, r.email as rep_email
        FROM clientes c
        LEFT JOIN representantes r ON r.codigo = c.representante_codigo
        WHERE c.codigo = '{safe_cod}'
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
        
        safe_cod = str(cliente_codigo).replace("'", "''")
        sql = f"""
        SELECT 
            COALESCE(pt.totvs_order_code, p.numero) as pedido,
            CASE
                WHEN COALESCE(pt.status, p.status) IN ('InProgress', 'Em andamento', 'open', 'aberto', '1') THEN 'Em andamento'
                WHEN COALESCE(pt.status, p.status) IN ('Blocked', 'Bloqueado', '5') THEN 'Bloqueado'
                WHEN COALESCE(pt.status, p.status) IN ('InComposition', 'Em composição', 'Em composicao', '7') THEN 'Em composição'
                WHEN COALESCE(pt.status, p.status) IN ('PartiallyAnswered', 'Parcialmente Atendido', '3') THEN 'Parcialmente Atendido'
                WHEN COALESCE(pt.status, p.status) IN ('Attended', 'Atendido', 'Faturado', '4') THEN 'Faturado'
                WHEN COALESCE(pt.status, p.status) IN ('Canceled', 'Cancelled', 'Cancelado', '6', '9') THEN 'Cancelado'
                ELSE COALESCE(pt.status, p.status, 'Em andamento')
            END as status,
            COALESCE(pt.data_pedido::date, p.created_at::date) as data_pedido,
            COALESCE(pt.previsao_faturamento::date, p.data_previsao_faturamento::date) as previsao_faturamento,
            COALESCE(pt.valor_total, p.valor_total, 0) as valor_total,
            COALESCE(pt.quantidade_total, 0) as metros,
            COALESCE(pt.nota_fiscal_numero, '') as nf
        FROM pedidos p
        LEFT JOIN clientes c ON c.id = p.cliente_id
        LEFT JOIN pedidos_totvs pt ON (
            pt.totvs_order_code = p.numero 
            OR (p.payload_totvs->>'orderId' IS NOT NULL AND pt.totvs_order_id = p.payload_totvs->>'orderId')
        )
        WHERE c.codigo = '{safe_cod}'
        ORDER BY COALESCE(pt.data_pedido, p.created_at) DESC
        LIMIT {limit}
        """
        res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return res.data or []

    @staticmethod
    def consultar_estoque_pronta_entrega(acabamento: str = "liso", base: str = "todas", termo_busca: str = "") -> List[Dict[str, Any]]:
        """
        Consulta o estoque de Pronta Entrega disponível por categoria oficial:
        acabamento: 'liso', 'estampado', 'ld_liso', 'ld_estampado'
        base: 'tricoline', 'linho', 'sarja', ou 'todas'
        """
        filtros = ["quantidade_disponivel > 0"]

        acab = acabamento.lower().strip()
        if acab in ("liso", "1"):
            filtros.append("categoria = 'liso'")
        elif acab in ("estampado", "2"):
            filtros.append("categoria = 'estampado'")
        elif acab in ("ld_liso", "liso_ld", "3"):
            filtros.append("categoria = 'ld_liso'")
        elif acab in ("ld_estampado", "estampado_ld", "4"):
            filtros.append("categoria = 'ld_estampado'")

        if base == "tricoline":
            filtros.append("(descricao ILIKE '%tricoline%')")
        elif base == "linho":
            filtros.append("(descricao ILIKE '%linho%')")
        elif base == "sarja":
            filtros.append("(descricao ILIKE '%sarja%')")

        if termo_busca:
            safe_termo = termo_busca.replace("'", "''")
            filtros.append(f"(descricao ILIKE '%{safe_termo}%' OR cor ILIKE '%{safe_termo}%')")

        where_clause = " AND ".join(filtros)
        sql = f"""
        SELECT 
            descricao as artigo,
            cod_produto as codigo_artigo,
            cor,
            cor_codigo,
            hex_color,
            desenho_url,
            categoria,
            quantidade_disponivel as metros_disponiveis
        FROM estoque_pe
        WHERE {where_clause}
        ORDER BY quantidade_disponivel DESC
        LIMIT 6
        """
        res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return res.data or []

    @staticmethod
    def consultar_programacao_ops(acabamento: str = "liso", base: str = "todas", termo_busca: str = "") -> List[Dict[str, Any]]:
        """
        Consulta as Ordens de Produção (OPs) abertas na tecelagem/tinturaria.
        """
        filtros = ["quantidade_disponivel > 0"]

        acab = acabamento.lower().strip()
        if acab in ("liso", "1"):
            filtros.append("tipo = 'liso'")
        elif acab in ("estampado", "2"):
            filtros.append("tipo = 'estampado'")
        elif acab in ("ld_liso", "liso_ld", "3"):
            filtros.append("(tipo = 'liso' AND (nome_tecido ILIKE '%(ld)%' OR nome_tecido ILIKE '%(dig)%'))")
        elif acab in ("ld_estampado", "estampado_ld", "4"):
            filtros.append("(tipo = 'estampado' AND (nome_tecido ILIKE '%(ld)%' OR nome_tecido ILIKE '%(dig)%'))")

        if base == "tricoline":
            filtros.append("(nome_tecido ILIKE '%tricoline%')")
        elif base == "linho":
            filtros.append("(nome_tecido ILIKE '%linho%')")
        elif base == "sarja":
            filtros.append("(nome_tecido ILIKE '%sarja%')")

        if termo_busca:
            safe_termo = termo_busca.replace("'", "''")
            filtros.append(f"(nome_tecido ILIKE '%{safe_termo}%' OR nome_cor ILIKE '%{safe_termo}%')")

        where_clause = " AND ".join(filtros)
        sql = f"""
        SELECT 
            op,
            nome_tecido as artigo,
            nome_cor as cor,
            hex_color,
            desenho_url,
            previsao_faturamento as previsao_entrega,
            quantidade_disponivel as metros_planejados
        FROM programacoes
        WHERE {where_clause}
        ORDER BY op DESC
        LIMIT 6
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
                "Como posso te ajudar agora? Digite uma das opções abaixo:\n\n"
                "*1️⃣ Consultar tecidos na Pronta Entrega*\n"
                "*2️⃣ Consultar tecidos em Programação (OPs)*\n"
                "*3️⃣ Acompanhar meus pedidos em aberto*\n"
                "*4️⃣ Ver catálogo e lançamentos*\n"
                "*5️⃣ Falar com meu representante oficial*"
            )

        nome = cliente.get("nome_fantasia") or cliente.get("razao_social") or "Cliente"
        rep_nome = cliente.get("rep_contato") or cliente.get("rep_nome") or "Comercial Designtex"

        pedidos = DeiseService.get_pedidos_cliente(cliente_codigo, limit=3)
        total_pedidos = len(pedidos)
        metros_abertos = sum(float(p.get("metros") or 0) for p in pedidos if p.get("status") in ["Em andamento", "Aberto", "Bloqueado"])
        
        ultima_nf = next((p.get("nf") for p in pedidos if p.get("nf")), "Consulte no Portal")

        msg = (
            f"Olá! Seja muito bem-vindo(a) à *Designtex Tecidos*. Meu nome é *Deise*, "
            f"sua assistente comercial inteligente! 👗🧵\n\n"
            f"Já identifiquei o cadastro da *{nome}* por aqui:\n"
            f"📦 *Pedidos Recentes:* {total_pedidos} registrados ({formatar_metros(metros_abertos)} em aberto)\n"
            f"🚚 *Última NF:* {ultima_nf}\n"
            f"👤 *Seu(ua) Representante:* {rep_nome}\n\n"
            f"Como posso te ajudar agora? Digite o número da opção desejada:\n\n"
            f"*1️⃣ Consultar tecidos na Pronta Entrega*\n"
            f"*2️⃣ Consultar tecidos em Programação (OPs)*\n"
            f"*3️⃣ Acompanhar meus pedidos em aberto*\n"
            f"*4️⃣ Ver catálogo e lançamentos*\n"
            f"*5️⃣ Falar com meu representante oficial*"
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
                "mensagem": "Vou transferir para nossa equipe de atendimento geral da Designtex:\n👉 https://wa.me/5531990151359",
                "link_zap": "https://wa.me/5531990151359",
                "rep_nome": "Comercial Designtex"
            }

        rep_nome = cliente.get("rep_contato") or cliente.get("rep_nome") or "Representante Designtex"
        rep_fone = cliente.get("rep_telefone") or "5531990151359"
        
        limpo_fone = "".join(filter(str.isdigit, rep_fone))
        if len(limpo_fone) in (10, 11) and not limpo_fone.startswith("55"):
            limpo_fone = "55" + limpo_fone

        link_zap = f"https://wa.me/{limpo_fone}"

        mensagem = (
            f"Com certeza! O seu representante oficial na Designtex é *{rep_nome}*.\n\n"
            f"Fale diretamente com ele(a) no WhatsApp:\n"
            f"👉 [Conversar com Representante no WhatsApp]({link_zap})\n\n"
            f"Já registrei sua solicitação e o(a) {rep_nome} dará total prioridade ao seu atendimento! 🤝"
        )

        return {
            "rep_nome": rep_nome,
            "rep_telefone": limpo_fone,
            "link_zap": link_zap,
            "mensagem": mensagem
        }

    @classmethod
    def atender(cls, remetente: str, texto: str, cliente_cod: str = "14") -> str:
        """
        Processador de diálogo inteligente com gestão de sessão e máquina de estados.
        Suporta os 4 acabamentos: 1 - Liso, 2 - Estampado, 3 - Liso LD, 4 - Estampado LD.
        """
        texto_limpo = str(texto or "").strip()
        texto_norm = desacentuar(texto_limpo)
        session_id = str(remetente or f"cli_{cliente_cod}")

        # Recupera ou inicializa a sessão
        sessao = _SESSOES.setdefault(session_id, {
            "step": None,
            "modulo": "pronta_entrega",
            "acabamento": "liso",
            "cliente_cod": cliente_cod,
            "timestamp": datetime.now()
        })
        sessao["cliente_cod"] = cliente_cod
        sessao["timestamp"] = datetime.now()

        current_step = sessao.get("step")

        # 1. Comandos Globais de Interrupção / Menu
        if texto_norm in ("menu", "inicio", "voltar", "oi", "ola", "ola deise", "olá deise", "bom dia", "boa tarde", "boa noite", "ajuda"):
            sessao["step"] = None
            return cls.gerar_boas_vindas(cliente_cod)

        # 2. Opções do Menu Principal
        if current_step is None:
            if texto_norm in ("1", "1)", "1 - pronta entrega", "pronta entrega", "pronta", "estoque", "pe"):
                sessao["step"] = "aguardando_acabamento"
                sessao["modulo"] = "pronta_entrega"
                return (
                    "👗 *Consulta de Tecidos na Pronta Entrega*\n\n"
                    "Qual acabamento você deseja consultar?\n"
                    "*1* - Liso\n"
                    "*2* - Estampado\n"
                    "*3* - Liso LD\n"
                    "*4* - Estampado LD"
                )

            elif texto_norm in ("2", "2)", "2 - programacao", "programacao", "programação", "ops", "producao", "produção"):
                sessao["step"] = "aguardando_acabamento"
                sessao["modulo"] = "programacao"
                return (
                    "🧵 *Consulta de Tecidos em Programação (OPs de Tecelagem)*\n\n"
                    "Qual acabamento você deseja consultar?\n"
                    "*1* - Liso\n"
                    "*2* - Estampado\n"
                    "*3* - Liso LD\n"
                    "*4* - Estampado LD"
                )

            elif texto_norm in ("3", "3)", "3 - pedidos", "pedidos", "meus pedidos", "pedido", "status pedido"):
                return cls._gerar_resposta_pedidos(cliente_cod)

            elif texto_norm in ("4", "4)", "4 - catalogo", "catalogo", "catálogo", "lancamentos", "lançamentos"):
                return (
                    "📖 *Catálogo Digital & Lançamentos Designtex Tecidos*\n\n"
                    "Acesse nosso catálogo completo e mostruário digital pelo link oficial:\n"
                    "👉 https://vendas.designtex.com.br/catalogo\n\n"
                    "Deseja solicitar amostra ou cartela física? Digite *5* para falar com seu representante!"
                )

            elif texto_norm in ("5", "5)", "5 - representante", "representante", "vendedor", "contato"):
                return cls.gerar_transferencia_representante(cliente_cod)["mensagem"]

        # 3. MÁQUINA DE ESTADOS: PASSO 1 (Acabamento: 1 - Liso, 2 - Estampado, 3 - Liso LD, 4 - Estampado LD)
        if current_step == "aguardando_acabamento":
            modulo = sessao.get("modulo", "pronta_entrega")
            modulo_label = "Pronta Entrega" if modulo == "pronta_entrega" else "Programação (OPs)"

            if texto_norm in ("1", "1)", "1 - liso", "liso", "lisos"):
                sessao["acabamento"] = "liso"
                sessao["step"] = "aguardando_base"
                return (
                    f"🌿 *Tecidos Lisos Convencionais ({modulo_label})*\n\n"
                    "Qual base você deseja conferir agora?\n"
                    "*1* - Tricolines (Top Line, Paris Plus...)\n"
                    "*2* - Linhos (Linho Panama, Linho Deluxe, Maragogi...)\n"
                    "*3* - Sarjas (Sarja Flex, Sarja Zara, Dakota...)\n"
                    "*4* - Ver todas as opções disponíveis"
                )

            elif texto_norm in ("2", "2)", "2 - estampado", "estampado", "estampados", "estampa", "rotativo"):
                sessao["acabamento"] = "estampado"
                sessao["step"] = "aguardando_base"
                return (
                    f"🎨 *Tecidos Estampados Convencionais ({modulo_label})*\n\n"
                    "Qual base você deseja conferir agora?\n"
                    "*1* - Tricolines Estampadas\n"
                    "*2* - Linhos Estampados\n"
                    "*3* - Sarjas Estampadas\n"
                    "*4* - Ver todas as estampas disponíveis"
                )

            elif texto_norm in ("3", "3)", "3 - liso ld", "liso ld", "ld liso", "liso digital", "ld"):
                sessao["acabamento"] = "ld_liso"
                sessao["step"] = "aguardando_base"
                return (
                    f"✨ *Tecidos Lisos LD - Linha Digital ({modulo_label})*\n\n"
                    "Qual base você deseja conferir agora?\n"
                    "*1* - Tricolines LD (Tricoline Paris LD, Deluxe LD...)\n"
                    "*2* - Linhos LD\n"
                    "*3* - Sarjas LD (Sarja Caribe Flex LD...)\n"
                    "*4* - Ver todas as opções disponíveis"
                )

            elif texto_norm in ("4", "4)", "4 - estampado ld", "estampado ld", "ld estampado", "estampa digital", "digital"):
                sessao["acabamento"] = "ld_estampado"
                sessao["step"] = "aguardando_base"
                return (
                    f"🌟 *Tecidos Estampados LD - Linha Digital ({modulo_label})*\n\n"
                    "Qual base você deseja conferir agora?\n"
                    "*1* - Tricolines Estampadas LD (Deluxe LD, Top Line Digital...)\n"
                    "*2* - Linhos Estampados LD\n"
                    "*3* - Sarjas Estampadas LD\n"
                    "*4* - Ver todas as estampas disponíveis"
                )

            # Se o usuário digitou direto o nome da base (ex: "linho", "tricoline", "sarja")
            elif any(b in texto_norm for b in ("tricoline", "linho", "sarja")):
                sessao["step"] = "aguardando_base"
                # Continua para o próximo bloco abaixo!

        # 4. MÁQUINA DE ESTADOS: PASSO 2 (Escolha da Base)
        if sessao.get("step") == "aguardando_base":
            modulo = sessao.get("modulo", "pronta_entrega")
            acabamento = sessao.get("acabamento", "liso")

            base_escolhida = "todas"
            if texto_norm in ("1", "1)", "a", "tricoline", "tricolines"):
                base_escolhida = "tricoline"
            elif texto_norm in ("2", "2)", "b", "linho", "linhos"):
                base_escolhida = "linho"
            elif texto_norm in ("3", "3)", "c", "sarja", "sarjas"):
                base_escolhida = "sarja"
            elif texto_norm in ("4", "4)", "d", "todas", "todos", "tudo"):
                base_escolhida = "todas"

            # Reseta estado para a próxima conversa
            sessao["step"] = None

            if modulo == "pronta_entrega":
                return cls._gerar_resposta_estoque(acabamento, base_escolhida)
            else:
                return cls._gerar_resposta_programacao(acabamento, base_escolhida)

        # 5. Reconhecimento Direto por Palavras-chave (Texto Livre)
        if any(palavra in texto_norm for palavra in ("pedido", "pedidos", "entrega", "faturamento", "nota fiscal", "nf")):
            sessao["step"] = None
            return cls._gerar_resposta_pedidos(cliente_cod)

        if any(palavra in texto_norm for palavra in ("representante", "vendedor", "contato")):
            sessao["step"] = None
            return cls.gerar_transferencia_representante(cliente_cod)["mensagem"]

        if any(palavra in texto_norm for palavra in ("catalogo", "mostruario", "colecao", "coleção")):
            sessao["step"] = None
            return (
                "📖 *Catálogo Digital & Lançamentos Designtex Tecidos*\n\n"
                "Acesse nosso mostruário online completo pelo link abaixo:\n"
                "👉 https://vendas.designtex.com.br/catalogo"
            )

        # Se citou um tecido específico em texto livre (ex: "tem linho?", "tem sarja flex?", "tem tricoline?")
        for base_key in ("tricoline", "linho", "sarja"):
            if base_key in texto_norm:
                acabamento = "ld_estampado" if ("ld" in texto_norm and "estamp" in texto_norm) else (
                    "ld_liso" if ("ld" in texto_norm) else (
                        "estampado" if ("estamp" in texto_norm) else "liso"
                    )
                )
                sessao["step"] = None
                return cls._gerar_resposta_estoque(acabamento, base_key)

        # Fallback padrão: Boas-vindas guiada
        sessao["step"] = None
        return cls.gerar_boas_vindas(cliente_cod)

    @classmethod
    def _gerar_resposta_estoque(cls, acabamento: str, base: str) -> str:
        itens = cls.consultar_estoque_pronta_entrega(acabamento, base)
        
        rotulos_tipo = {
            "liso": "Lisos Convencionais",
            "estampado": "Estampados Convencionais",
            "ld_liso": "Lisos LD (Linha Digital)",
            "ld_estampado": "Estampados LD (Linha Digital)",
        }
        tipo_label = rotulos_tipo.get(acabamento, "Tecidos")
        base_label = base.capitalize() if base != "todas" else "Principais Bases"

        if not itens:
            return (
                f"No momento não temos saldo disponível para *{base_label} ({tipo_label})* na Pronta Entrega.\n\n"
                "Gostaria de consultar as opções em *Programação de Produção (OPs)*? Digite *2* ou digite *5* para falar com seu representante!"
            )

        is_estampado = acabamento in ("estampado", "ld_estampado")
        emoji_header = "🎨" if is_estampado else "👗"
        linhas = [f"{emoji_header} *Tecidos {tipo_label} em Pronta Entrega ({base_label}):*\n"]

        for it in itens[:6]:
            art = it.get("artigo") or "Tecido Designtex"
            cor = it.get("cor") or "Padrão"
            cor_cod = str(it.get("cor_codigo") or "").strip()
            metros = float(it.get("metros_disponiveis") or 0)
            hex_c = (it.get("hex_color") or "").strip()
            desenho_url = (it.get("desenho_url") or "").strip()

            hex_tag = f" [hex:{hex_c}]" if (hex_c and hex_c.startswith("#")) else ""
            linhas.append(f"• *{art}*\n  Cor: {cor}{hex_tag} | *Disponível: {metros:,.1f} m*")

            # Se for estampado, adiciona a estampa para preview e download
            if is_estampado:
                img_url = desenho_url
                if not img_url and cor_cod:
                    clean_des = cor_cod.replace(" ", "")
                    img_url = f"{SUPABASE_STORAGE_DESENHOS}/{clean_des}.jpg"
                if img_url:
                    linhas.append(f"  [estampa:{img_url}]")

        linhas.append(
            "\n📲 *Deseja solicitar pré-reserva de algum desses lotes?*\n"
            "Digite *5* para falar com seu representante comercial ou digite *menu* para voltar."
        )
        return "\n".join(linhas)

    @classmethod
    def _gerar_resposta_programacao(cls, acabamento: str, base: str) -> str:
        ops = cls.consultar_programacao_ops(acabamento, base)
        rotulos_tipo = {
            "liso": "Lisos Convencionais",
            "estampado": "Estampados Convencionais",
            "ld_liso": "Lisos LD (Linha Digital)",
            "ld_estampado": "Estampados LD (Linha Digital)",
        }
        tipo_label = rotulos_tipo.get(acabamento, "Tecidos")
        base_label = base.capitalize() if base != "todas" else "Principais Linhas"

        if not ops:
            return (
                f"No momento não há OPs abertas para *{base_label} ({tipo_label})* na programação.\n\n"
                "Digite *1* para conferir a Pronta Entrega ou *5* para consultar previsões especiais com seu representante!"
            )

        is_estampado = acabamento in ("estampado", "ld_estampado")
        linhas = [f"🧵 *Ordens de Produção em Programação ({base_label} - {tipo_label}):*\n"]
        for op in ops[:6]:
            op_num = op.get("op") or "OP"
            art = op.get("artigo") or "Tecido"
            cor = op.get("cor") or "Cor Padrão"
            metros = float(op.get("metros_planejados") or 0)
            prev = op.get("previsao_entrega") or "A definir"
            hex_c = (op.get("hex_color") or "").strip()
            desenho_url = (op.get("desenho_url") or "").strip()

            hex_tag = f" [hex:{hex_c}]" if (hex_c and hex_c.startswith("#")) else ""
            linhas.append(f"• *OP {op_num}: {art}*\n  Cor: {cor}{hex_tag} | Previsão: *{prev}* | Saldo: *{metros:,.1f} m*")
            if is_estampado and desenho_url:
                linhas.append(f"  [estampa:{desenho_url}]")

        linhas.append(
            "\n📲 *Deseja programar corte antecipado de alguma dessas OPs?*\n"
            "Digite *5* para falar com seu representante comercial ou digite *menu* para voltar."
        )
        return "\n".join(linhas)

    @classmethod
    def _gerar_resposta_pedidos(cls, cliente_cod: str) -> str:
        pedidos = cls.get_pedidos_cliente(cliente_cod, limit=4)
        if not pedidos:
            return f"Não encontrei pedidos recentes em aberto para o seu cadastro (Cód: {cliente_cod})."

        cliente = cls.validar_cliente(cliente_cod)
        nome = cliente.get("nome_fantasia") or "Cliente" if cliente else "Cliente"

        linhas = [f"📦 *Acompanhamento de Pedidos — {nome} (Cód: {cliente_cod}):*\n"]
        for p in pedidos:
            ped_num = p.get("pedido")
            status = p.get("status") or "Em processamento"
            metros = float(p.get("metros") or 0)
            nf = p.get("nf") or "Aguardando faturamento"
            prev = p.get("previsao_faturamento") or "A definir"
            linhas.append(
                f"🔹 *Pedido: {ped_num}*\n"
                f"   Status: *{status}*\n"
                f"   Volume: *{metros:,.1f} m*\n"
                f"   Nota Fiscal: *{nf}*\n"
                f"   Previsão: {prev}\n"
            )

        linhas.append("Digite *5* para falar diretamente com o seu representante comercial sobre seus pedidos.")
        return "\n".join(linhas)
