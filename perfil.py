import json
from datetime import datetime
from pathlib import Path

ARQUIVO_PERFIL = Path(__file__).parent / "meu_perfil.json"
PERFIL_VAZIO = {"vistos": [], "watchlist": []}


def carregar():
    if not ARQUIVO_PERFIL.exists():
        return dict(PERFIL_VAZIO)
    try:
        dados = json.loads(ARQUIVO_PERFIL.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(PERFIL_VAZIO)

    dados.setdefault("vistos", [])
    dados.setdefault("watchlist", [])
    return dados


def salvar(perfil):
    ARQUIVO_PERFIL.write_text(
        json.dumps(perfil, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def ja_assistiu(perfil, titulo):
    return titulo in perfil["vistos"]


def marcar_visto(titulo):
    perfil = carregar()
    if titulo not in perfil["vistos"]:
        perfil["vistos"].append(titulo)
        salvar(perfil)
        return True
    return False


def salvar_para_depois(item):
    perfil = carregar()

    if any(salvo["titulo"] == item["titulo"] for salvo in perfil["watchlist"]):
        return False

    perfil["watchlist"].append({
        "titulo": item["titulo"],
        "tipo": item["tipo"],
        "ano": item["ano"],
        "nota": item["nota"],
        "duracao": item["duracao"],
        "link": item["link"],
        "salvo_em": datetime.now().strftime("%d/%m/%Y"),
    })
    salvar(perfil)
    return True


def remover_da_watchlist(titulo):
    perfil = carregar()
    antes = len(perfil["watchlist"])
    perfil["watchlist"] = [s for s in perfil["watchlist"] if s["titulo"] != titulo]
    salvar(perfil)
    return len(perfil["watchlist"]) < antes
