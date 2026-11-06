"""
Script Cross-Platform para Conectar a Agente DEISE ao WhatsApp
Funciona no Windows (CMD / PowerShell), Linux e macOS.
"""

import sys, os, time, subprocess, urllib.request, json

API_KEY = "conexo_deise_secret_2026"

def main():
    print("=" * 70)
    print("   CONECTANDO A AGENTE DEISE (WHATSAPP DESIGNTEX TECIDOS)")
    print("=" * 70)

    # 1. Verificar se estamos rodando em uma VPS com Docker ou no Windows
    docker_disponivel = False
    try:
        res = subprocess.run(["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            docker_disponivel = True
            print(f"✅ Docker detectado: {res.stdout.strip()}")
    except FileNotFoundError:
        pass

    if docker_disponivel:
        print("🚀 Subindo containers da Evolution API via Docker...")
        subprocess.run(["docker", "compose", "up", "-d"])
        print("⏳ Aguardando Evolution API inicializar...")
        time.sleep(10)
        base_url = "http://127.0.0.1:8080"
    else:
        # Se estiver rodando no Windows, direciona para a VPS conexo.dev
        print("ℹ️  Executando no ambiente Windows.")
        print("📡 Conectando ao servidor remoto do CONEXO (conexo.dev)...")
        base_url = "https://conexo.dev/evolution"

    print("\n📱 Registrando instância 'deise' para o número +55 31 99015-1359...")
    try:
        url_create = f"{base_url}/instance/create"
        payload = json.dumps({
            "instanceName": "deise",
            "token": "deise_secret_token",
            "number": "5531990151359",
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }).encode("utf-8")
        req = urllib.request.Request(
            url_create,
            data=payload,
            headers={"Content-Type": "application/json", "apikey": API_KEY},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            print("✅ Instância criada/verificada com sucesso!")
    except Exception as e:
        print(f"Nota: {e} (instância pode já estar criada, prosseguindo para o QR Code)")

    print("\n" + "=" * 70)
    print("      QR CODE DE CONEXÃO DA DEISE (WHATSAPP BUSINESS)")
    print("=" * 70)
    print("1. Abra o WhatsApp Business no celular (+55 31 99015-1359)")
    print("2. Toque nos 3 pontinhos -> 'Aparelhos Conectados'")
    print("3. Toque em 'Conectar um aparelho'")
    print("4. Abra a URL abaixo no seu navegador para ver o QR Code:")
    print(f"\n👉 {base_url}/instance/connect/deise\n")
    print("=" * 70)

if __name__ == "__main__":
    main()
