import json
import re
import time
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

API_SERIES = "https://api.tvmaze.com/shows"
API_FILMES = "https://v3-cinemeta.strem.io/catalog/movie/top"

TIMEOUT = 25
ARQUIVO_CACHE = Path(__file__).parent / "cache_catalogo.json"
VALIDADE_CACHE_HORAS = 12

GENEROS = {
    "acao": ["Action"],
    "aventura": ["Adventure"],
    "animacao": ["Animation"],
    "comedia": ["Comedy"],
    "crime": ["Crime"],
    "documentario": ["Documentary"],
    "drama": ["Drama"],
    "familia": ["Family"],
    "fantasia": ["Fantasy"],
    "guerra": ["War"],
    "misterio": ["Mystery"],
    "romance": ["Romance"],
    "ficcao": ["Sci-Fi", "Science-Fiction"],
    "suspense": ["Thriller"],
    "terror": ["Horror"],
}


def sem_acento(texto):
    normalizado = unicodedata.normalize("NFKD", texto or "")
    limpo = "".join(c for c in normalizado if not unicodedata.combining(c))
    return limpo.lower().strip()


def traduzir_genero(entrada):
    return GENEROS.get(sem_acento(entrada))


def generos_disponiveis():
    return sorted(GENEROS)


def limpar_sinopse(bruto):
    if not bruto:
        return "Sinopse nao disponivel."
    texto = BeautifulSoup(bruto, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", texto) or "Sinopse nao disponivel."


def _minutos(valor):
    if isinstance(valor, (int, float)) and valor:
        return int(valor)
    if isinstance(valor, str):
        achado = re.search(r"\d+", valor)
        if achado:
            return int(achado.group())
    return None


def _nota(valor):
    try:
        convertida = float(valor)
    except (TypeError, ValueError):
        return None
    return convertida if convertida > 0 else None


def _ano(data):
    achado = re.search(r"\d{4}", str(data or ""))
    return achado.group() if achado else "----"


def buscar_series(paginas=1):
    titulos = []

    for pagina in range(paginas):
        resposta = requests.get(API_SERIES, params={"page": pagina}, timeout=TIMEOUT)
        resposta.raise_for_status()

        for serie in resposta.json():
            imagem = serie.get("image") or {}
            titulos.append({
                "tipo": "serie",
                "titulo": serie.get("name", "Sem titulo"),
                "ano": _ano(serie.get("premiered")),
                "nota": _nota((serie.get("rating") or {}).get("average")),
                "duracao": _minutos(serie.get("averageRuntime") or serie.get("runtime")),
                "generos": serie.get("genres") or [],
                "sinopse": limpar_sinopse(serie.get("summary")),
                "elenco": [],
                "extra_rotulo": "Status",
                "extra": serie.get("status") or "",
                "link": serie.get("url", ""),
                "poster": imagem.get("medium", ""),
            })

    return titulos


def buscar_filmes(generos_api=None, paginas=3):
    titulos = []
    nome_genero = generos_api[0] if generos_api else None

    for pagina in range(paginas):
        partes = [API_FILMES]
        if nome_genero:
            partes.append("genre=" + nome_genero)
        if pagina:
            partes.append("skip=" + str(pagina * 50))
        url = "/".join(partes) + ".json"

        resposta = requests.get(url, timeout=TIMEOUT)
        if resposta.status_code != 200:
            break

        filmes = resposta.json().get("metas", [])
        if not filmes and nome_genero:
            nome_genero = None
            continue

        for filme in filmes:
            codigo_imdb = filme.get("imdb_id", "")
            titulos.append({
                "tipo": "filme",
                "titulo": filme.get("name", "Sem titulo"),
                "ano": _ano(filme.get("released")),
                "nota": _nota(filme.get("imdbRating")),
                "duracao": _minutos(filme.get("runtime")),
                "generos": filme.get("genre") or [],
                "sinopse": limpar_sinopse(filme.get("description")),
                "elenco": (filme.get("cast") or [])[:3],
                "extra_rotulo": "Direcao",
                "extra": ", ".join((filme.get("director") or [])[:1]),
                "link": "https://www.imdb.com/title/" + codigo_imdb + "/",
                "poster": filme.get("poster", ""),
            })

    return titulos


def _cache_valido(dados, chave):
    if not dados or dados.get("chave") != chave:
        return False
    idade_horas = (time.time() - dados.get("gravado_em", 0)) / 3600
    return idade_horas < VALIDADE_CACHE_HORAS


def montar_catalogo(tipo, genero_api=None, usar_cache=True):
    chave = tipo + "|" + (genero_api or "todos")

    if usar_cache and ARQUIVO_CACHE.exists():
        try:
            salvo = json.loads(ARQUIVO_CACHE.read_text(encoding="utf-8"))
            if _cache_valido(salvo, chave):
                print("[cache] " + str(len(salvo["titulos"])) + " titulos lidos do disco.")
                return salvo["titulos"]
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    print("[rede] Consultando as APIs de filmes e series...")
    titulos = []
    if tipo in ("serie", "ambos"):
        titulos += buscar_series(paginas=1)
    if tipo in ("filme", "ambos"):
        titulos += buscar_filmes(generos_api=[genero_api] if genero_api else None)

    ARQUIVO_CACHE.write_text(
        json.dumps({"chave": chave, "gravado_em": time.time(), "titulos": titulos}),
        encoding="utf-8",
    )
    print("[rede] " + str(len(titulos)) + " titulos baixados.")
    return titulos


def limpar_cache():
    if ARQUIVO_CACHE.exists():
        ARQUIVO_CACHE.unlink()
        return True
    return False
