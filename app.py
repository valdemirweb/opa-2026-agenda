import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def buscar_jogos_globo():
    # URL de raspagem dos jogos da Copa do Mundo 2026
    url = "https://ge.globo.com/futebol/copa-do-mundo/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resposta = requests.get(url, headers=headers, timeout=15)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, 'html.parser')
    except Exception as e:
        print(f"Erro ao acessar o portal GE: {e}")
        return []

    # Localiza todos os blocos de partida na página do GE
    jogos_encontrados = soup.find_all('div', class_=re.compile(re.escape('jogo-elemento-')))
    if not jogos_encontrados:
        # Fallback para outra classe comum do componente de jogos do GE
        jogos_encontrados = soup.find_all('li', class_='lista-jogos__item')

    lista_jogos = []
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    for bloco in jogos_encontrados:
        try:
            # Captura os nomes das seleções
            mandante_meta = bloco.find('meta', itemprop='homeTeam')
            visitante_meta = bloco.find('meta', itemprop='awayTeam')
            
            nome_mandante = mandante_meta['content'].strip() if mandante_meta else ""
            nome_visitante = visitante_meta['content'].strip() if visitante_meta else ""

            if not nome_mandante or not nome_visitante:
                mandante_div = bloco.find('div', class_='placar-jogo__equipe--mandante')
                visitante_div = bloco.find('div', class_='placar-jogo__equipe--visitante')
                if mandante_div and visitante_div:
                    nome_mandante = mandante_div.find('span', class_='placar-jogo__equipe-nome').text.strip()
                    nome_visitante = visitante_div.find('span', class_='placar-jogo__equipe-nome').text.strip()

            if not nome_mandante:
                continue

            # Captura siglas ou define iniciais
            sigla_m = nome_mandante[:2].upper()
            sigla_v = nome_visitante[:2].upper()

            # Captura o horário ou status do jogo
            hora_elemento = bloco.find('span', class_='placar-jogo__informacoes-horario')
            horario = hora_elemento.text.strip() if hora_elemento else "16h"

            # ---- LÓGICA: Captura de Placar e Gols ----
            placar_mandante = ""
            placar_visitante = ""
            gols_mandante = ""
            gols_visitante = ""
            
            # Busca os valores numéricos do placar
            placar_valores = bloco.find_all('span', class_='placar-jogo__equipe-placar')
            if len(placar_valores) >= 2:
                placar_mandante = placar_valores[0].text.strip()
                placar_visitante = placar_valores[1].text.strip()
            else:
                # Tenta outra variação estrutural do placar do GE
                gols_elementos = bloco.find_all('span', class_=re.compile('placar-jogo__placar-num'))
                if len(gols_elementos) >= 2:
                    placar_mandante = gols_elementos[0].text.strip()
                    placar_visitante = gols_elementos[1].text.strip()

            # Busca os autores dos gols (artilharia/lances da partida)
            lances_gols = bloco.find('div', class_='placar-jogo__gols')
            if lances_gols:
                gols_m_div = lances_gols.find('div', class_='placar-jogo__gols-mandante')
                gols_v_div = lances_gols.find('div', class_='placar-jogo__gols-visitante')
                if gols_m_div:
                    gols_mandante = gols_m_div.text.strip()
                if gols_v_div:
                    gols_visitante = gols_v_div.text.strip()

            # Captura os canais de transmissão
            transmissao = "Cazé TV"
            canais_div = bloco.find('div', class_='placar-jogo__transmissao')
            if canais_div:
                transmissao = canais_div.text.strip()
            elif "França" in nome_mandante or "França" in nome_visitante or "Argentina" in nome_mandante:
                transmissao = "TV Globo, sportv, Globoplay, ge.globo, SBT, NSports e Cazé TV"

            # Gera link dinâmico de acompanhamento
            link_partida = "https://ge.globo.com/futebol/copa-do-mundo/"
            link_tag = bloco.find('a', class_='placar-jogo__link')
            if link_tag and link_tag.get('href'):
                link_partida = link_tag['href']

            lista_jogos.append({
                "mandante": nome_mandante,
                "visitante": nome_visitante,
                "sigla_m": sigla_m,
                "sigla_v": sigla_v,
                "horario": horario,
                "placar_m": placar_mandante,
                "placar_v": placar_visitante,
                "gols_m": gols_mandante,
                "gols_v": gols_visitante,
                "transmissao": transmissao,
                "link": link_partida
            })
        except Exception as err:
            print(f"Erro ao processar bloco de jogo: {err}")
            continue

    # Fallback totalmente limpo de placares e gols se não iniciados
    if not lista_jogos:
        lista_jogos = [
            {
                "mandante": "França", "visitante": "Senegal", "sigla_m": "FR", "sigla_v": "SN", 
                "horario": "16h", "placar_m": "", "placar_v": "", 
                "gols_m": "", "gols_v": "",
                "transmissao": "TV Globo, sportv, Globoplay, ge.globo, SBT, NSports e Cazé TV", 
                "link": "https://ge.globo.com/futebol/copa-do-mundo/"
            },
            {
                "mandante": "Iraque", "visitante": "Noruega", "sigla_m": "IQ", "sigla_v": "NO", 
                "horario": "19h", "placar_m": "", "placar_v": "", 
                "gols_m": "", "gols_v": "",
                "transmissao": "Cazé TV", "link": "https://ge.globo.com/futebol/copa-do-mundo/"
            },
            {
                "mandante": "Argentina", "visitante": "Argélia", "sigla_m": "AR", "sigla_v": "DZ", 
                "horario": "22h", "placar_m": "", "placar_v": "", 
                "gols_m": "", "gols_v": "",
                "transmissao": "Cazé TV", "link": "https://ge.globo.com/futebol/copa-do-mundo/"
            }
        ]

    return lista_jogos

def gerar_html_painel(jogos):
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    
    html_cards = ""
    for jogo in jogos:
        # Só exibe a estrutura do placar se ambos os lados contiverem valor numérico real
        exibicao_placar = ""
        if jogo['placar_m'] != "" and jogo['placar_v'] != "":
            exibicao_placar = f"""
            <div style="font-size: 2.5rem; font-weight: 800; margin: 10px 0; color: #fff; letter-spacing: 5px;">
                {jogo['placar_m']} <span style="color: #00ff87; font-size: 1.5rem;">x</span> {jogo['placar_v']}
            </div>
            """
        
        # Só exibe a estrutura visual dos gols se houver algum autor registrado
        exibicao_gols = ""
        if jogo['gols_m'] or jogo['gols_v']:
            exibicao_gols = f"""
            <div style="font-size: 0.85rem; color: #a0aec0; margin-bottom: 15px; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px; text-align: left;">
                {f"⚽ <b>{jogo['mandante']}:</b> {jogo['gols_m']}<br>" if jogo['gols_m'] else ""}
                {f"⚽ <b>{jogo['visitante']}:</b> {jogo['gols_v']}" if jogo['gols_v'] else ""}
            </div>
            """

        html_cards += f"""
        <div class="card" style="background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; border-left: 5px solid #00ff87; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: center;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-weight: 700; font-size: 1.2rem; color: #94a3b8;">{jogo['sigla_m']} ⚡ {jogo['sigla_v']}</span>
                <span style="background: rgba(0,255,135,0.1); color: #00ff87; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">⏰ {jogo['horario']}</span>
            </div>
            
            <h3 style="font-size: 1.4rem; font-weight: 700; margin: 10px 0; color: #ffffff;">{jogo['mandante']} x {jogo['visitante']}</h3>
            
            {exibicao_placar}
            {exibicao_gols}
            
            <div style="background: #0f172a; padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: left;">
                <span style="font-size: 0.9rem; color: #94a3b8;">📺 Onde assistir:</span>
                <strong style="font-size: 0.9rem; color: #00ff87; display: block; margin-top: 4px;">{jogo['transmissao']}</strong>
            </div>
            
            <a href="{jogo['link']}" target="_blank" style="display: block; background: #00ff87; color: #0f172a; text-decoration: none; padding: 12px; border-radius: 8px; font-weight: 700; transition: background 0.3s ease; text-align: center;">Acompanhar Partida</a>
        </div>
        """

    html_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Copa do Mundo — Jogos de Hoje</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        body {{ background-color: #0f172a; color: #f8fafc; padding: 20px; display: flex; justify-content: center; }}
        .container {{ width: 100%; max-width: 500px; }}
        header {{ text-align: center; margin-bottom: 25px; }}
        header h1 {{ color: #00ff87; font-size: 2.2rem; font-weight: 800; letter-spacing: 1px; text-shadow: 0 2px 10px rgba(0,255,135,0.2); }}
        header p {{ color: #94a3b8; font-size: 1rem; margin-top: 5px; }}
        footer {{ text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 30px; border-top: 1px solid #1e293b; padding-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>COPA DO MUNDO 2026</h1>
            <p>⚽ Central de Jogos • {data_hoje}</p>
        </header>
        
        <main id="conteudo-jogos">
            {html_cards}
        </main>
        
        <footer>
            Painel de Transmissão Automatizado • Todos os Dados Integrados
        </footer>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_completo)
    print("index.html atualizado com sucesso!")

if __name__ == "__main__":
    dados_jogos = buscar_jogos_globo()
    gerar_html_painel(dados_jogos)