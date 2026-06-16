import requests
from bs4 import BeautifulSoup
from datetime import datetime
import warnings
import re
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def obter_bandeira(texto_titulo):
    texto_lower = texto_titulo.lower()
    bandeiras = {
        "frança": "🇫🇷", "senegal": "🇸🇳", "irã": "🇮🇷", "nova zelândia": "🇳🇿",
        "argentina": "🇦🇷", "argélia": "🇩🇿", "iraque": "🇮🇶", "noruega": "🇳🇴",
        "áustria": "🇦🇹", "jordânia": "🇯🇴", "uruguai": "🇺🇾", "arábia saudita": "🇸🇦",
        "cabo verde": "🇨🇻", "espanha": "🇪🇸", "inglaterra": "🇬🇧", "croácia": "🇭🇷",
        "turquia": "🇹🇷", "paraguai": "🇵🇾", "estados unidos": "🇺🇸", "austrália": "🇦🇺",
        "bélgica": "🇧🇪", "egito": "🇪🇬", "brasil": "🇧🇷", "marrocos": "🇲🇦",
        "fortaleza": "🦁", "américa-mg": "🐰"
    }
    encontradas = []
    for pais, emoji in bandeiras.items():
        if pais in texto_lower:
            encontradas.append(emoji)
    if len(encontradas) >= 2:
        return f"{encontradas[0]} ⚡ {encontradas[1]}"
    elif len(encontradas) == 1:
        return encontradas[0]
    return "⚽"

def extrair_jogos_internos_do_guia(url, headers):
    jogos_extraidos = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup_artigo = BeautifulSoup(res.content, 'html.parser')
            elementos = soup_artigo.find_all(['p', 'li', 'h2', 'h3', 'strong'])
            
            for elem in elementos:
                texto = elem.get_text().strip()
                texto_lower = texto.lower()
                
                if "2022" in texto or "catar" in texto_lower or "foto:" in texto_lower or "by" in texto_lower:
                    continue
                
                if " x " in texto and len(texto) < 180:
                    horario_match = re.search(r'(\d{2}h\d{2}|\d{2}h|\d{2}:\d{2})', texto)
                    horario = horario_match.group(1) if horario_match else "Ao Vivo"
                    
                    onde_assistir = "Ver na transmissão"
                    if "onde assistir" in texto_lower:
                        partes_transmissao = re.split(r'(?i)onde assistir\s*:\s*', texto)
                        if len(partes_transmissao) > 1:
                            onde_assistir = partes_transmissao[1].strip()
                    
                    titulo_limpo = texto
                    if "onde assistir" in texto_lower:
                        titulo_limpo = re.split(r'(?i)onde assistir', titulo_limpo)[0]
                    
                    if horario_match:
                        titulo_limpo = titulo_limpo.replace(horario_match.group(1), "")
                    
                    titulo_limpo = re.sub(r'[-\–\—\(\)\.\,\:]', '', titulo_limpo)
                    titulo_limpo = re.sub(r'\s+', ' ', titulo_limpo).strip()
                    
                    if len(titulo_limpo) < 5 or " x " not in titulo_limpo.lower():
                        continue
                        
                    if not any(j['titulo'].lower() == titulo_limpo.lower() for j in jogos_extraidos):
                        jogos_extraidos.append({
                            "titulo": titulo_limpo,
                            "link": url,
                            "horario": horario,
                            "transmissao": onde_assistir,
                            "bandeira": obter_bandeira(titulo_limpo)
                        })
    except Exception as e:
        print(f"⚠️ Nota ao ler dados internos: {e}")
    return jogos_extraidos

def pegar_jogos_rss():
    url = "https://ge.globo.com/rss/ge/futebol/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    data_atual = datetime.today()
    string_hoje_url = data_atual.strftime('%d-%m-%Y')
    string_hoje_titulo = data_atual.strftime('%d/%m')
    data_formatada = data_atual.strftime('%d/%m/%Y')
    
    print(f"--- REGENERANDO CENTRAL WEB ({data_formatada}) ---")
    print("Corrigindo sintaxe e removendo alertas do VS Code...\n")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            itens = soup.find_all('item')
            
            if not itens:
                print("⚠️ Nenhuma informação encontrada no feed.")
                return
                
            jogos_finais = []
            
            for item in itens:
                titulo = item.find('title').text.strip() if item.find('title') else ""
                link = item.find('link').next_sibling.strip() if item.find('link') else ""
                if not link and item.find('link'):
                    link = item.find('link').text.strip()

                eh_link_de_jogo = "/jogo/" in link.lower()
                eh_guia_transmissao = "onde assistir" in titulo.lower() or "veja jogos e horários" in titulo.lower()
                eh_de_hoje = string_hoje_url in link or string_hoje_titulo in titulo
                eh_blog = "/blogs/" in link.lower()
                eh_curiosidade = "curiosidades" in titulo.lower() or "viraliza" in titulo.lower()

                if titulo and (eh_link_de_jogo or eh_guia_transmissao) and eh_de_hoje and not (eh_blog or eh_curiosidade):
                    if eh_guia_transmissao:
                        jogos_internos = extrair_jogos_internos_do_guia(link, headers)
                        for ji in jogos_internos:
                            if not any(jf['titulo'].lower() == ji['titulo'].lower() for jf in jogos_finais):
                                jogos_finais.append(ji)
                    else:
                        titulo_limpo = titulo.replace(" - Copa do Mundo 2026 - globoesporte.com", "")
                        horario_match = re.search(r'(\d{2}h\d{2}|\d{2}h|\d{2}:\d{2})', titulo_limpo)
                        horario = horario_match.group(1) if horario_match else "Ao Vivo"
                        
                        if horario_match:
                            titulo_limpo = titulo_limpo.replace(horario_match.group(1), "").strip()
                        
                        if not any(jf['titulo'].lower() == titulo_limpo.lower() for jf in jogos_finais):
                            jogos_finais.append({
                                "titulo": titulo_limpo,
                                "link": link,
                                "horario": horario,
                                "transmissao": "Globo / sportv / ge",
                                "bandeira": obter_bandeira(titulo_limpo)
                            })
            
            html_cards = ""
            for jogo in jogos_finais:
                html_cards += f"""
                <div class="card">
                    <div class="card-header-info">
                        <span class="card-badge">{jogo['bandeira']}</span>
                        <span class="card-time">⏰ {jogo['horario']}</span>
                    </div>
                    <h3>{jogo['titulo']}</h3>
                    <div class="card-tv">
                        <span class="tv-label">📺 Onde assistir:</span>
                        <span class="tv-channels">{jogo['transmissao']}</span>
                    </div>
                    <a href="{jogo['link']}" target="_blank" class="btn-match">Acompanhar Partida</a>
                </div>"""
            
            if not html_cards:
                html_cards = "<p style='color: #fff; text-align: center;'>Nenhum confronto isolado encontrado para hoje. Atualize mais tarde!</p>"

            # Estrutura HTML limpa e unificada sem quebras em f-strings de CSS
            html_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Copa do Mundo — Jogos de Hoje</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        body {{
            background: linear-gradient(135deg, #0b0f19, #111827, #1f2937);
            min-height: 100vh;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-bottom: 3rem;
        }}
        .banner {{
            width: 100%;
            height: 220px;
            background: linear-gradient(rgba(11, 15, 25, 0.3), #0b0f19), 
                        url('https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80') center/cover no-repeat;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            padding-bottom: 1.5rem;
            text-align: center;
            box-shadow: inset 0 -30px 40px #0b0f19;
        }}
        .banner h1 {{
            font-size: 2.5rem;
            font-weight: 900;
            letter-spacing: 1px;
            background: linear-gradient(45deg, #ffd700, #00ff87);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
        }}
        .banner p {{
            color: #38bdf8;
            font-weight: 600;
            font-size: 1.1rem;
            margin-top: 0.2rem;
        }}
        .container {{
            max-width: 650px;
            width: 100%;
            padding: 0 1rem;
            margin-top: 1.5rem;
        }}
        .grid {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 1.8rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(to bottom, #ffd700, #00ff87);
            opacity: 0.7;
        }}
        .card:hover {{
            transform: scale(1.02);
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(0, 255, 135, 0.3);
            box-shadow: 0 10px 30px rgba(0, 255, 135, 0.1);
        }}
        .card-header-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.8rem;
        }}
        .card-badge {{
            font-size: 2rem;
        }}
        .card-time {{
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            padding: 0.4rem 0.8rem;
            border-radius: 30px;
            font-size: 0.85rem;
            font-weight: 700;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .card h3 {{
            font-size: 1.3rem;
            font-weight: 700;
            line-height: 1.4;
            color: #f3f4f6;
            margin-bottom: 0.8rem;
        }}
        .card-tv {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px dashed rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 0.7rem 1rem;
            margin-bottom: 1.2rem;
            font-size: 0.9rem;
        }}
        .tv-label {{
            color: #9ca3af;
            font-weight: 600;
            margin-right: 0.4rem;
        }}
        .tv-channels {{
            color: #00ff87;
            font-weight: 700;
        }}
        .btn-match {{
            display: block;
            text-align: center;
            background: linear-gradient(45deg, #10b981, #059669);
            color: #ffffff;
            text-decoration: none;
            font-weight: 700;
            padding: 0.9rem;
            border-radius: 12px;
            font-size: 1rem;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
            transition: all 0.2s ease;
        }}
        .btn-match:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
            filter: brightness(1.1);
        }}
        footer {{
            text-align: center;
            margin-top: 4rem;
            color: #4b5563;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="banner">
        <h1>Copa do Mundo 2026</h1>
        <p>⚽ Central de Jogos • {data_formatada}</p>
    </div>

    <div class="container">
        <main class="grid">
            {html_cards}
        </main>

        <footer>
            <p>Painel de Transmissão Automatizado • Todos os Dados Integrados</p>
        </footer>
    </div>
</body>
</html>"""

            with open("index.html", "w", encoding="utf-8") as f:
                f.write(html_completo)
                
            print("🚀 Dashboard estruturado com sucesso!")
            print("👉 O HTML foi corrigido e o aviso do VS Code irá sumir após rodar!")
                    
        else:
            print(f"❌ Erro ao acessar o Feed. Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    pegar_jogos_rss()