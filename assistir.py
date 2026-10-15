import argparse
import random
import sys
import textwrap
import time

import requests

import catalogo
import perfil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LARGURA = 72


def linha(caractere="-"):
    print("+" + caractere * LARGURA + "+")


def titulo_secao(texto):
    linha("=")
    print("|" + texto.center(LARGURA) + "|")
    linha("=")


def exibir_cartao(item, pontos, motivos):
    etiqueta = "[ " + item["tipo"].upper() + " ]"
    print()
    linha("=")
    cabecalho = " SUGESTAO DE HOJE"
    print("|" + cabecalho + etiqueta.rjust(LARGURA - len(cabecalho)) + "|")
    linha("=")

    print()
    print("  " + item["titulo"] + "  (" + item["ano"] + ")")

    nota = ("Nota " + str(item["nota"]) + "/10") if item["nota"] else "Sem nota"
    duracao = (str(item["duracao"]) + " min") if item["duracao"] else "duracao n/d"
    ficha = [nota, duracao]
    if item["generos"]:
        ficha.append(", ".join(item["generos"][:3]))
    print("  " + "   |   ".join(ficha))

    print()
    for parte in textwrap.wrap(item["sinopse"], width=LARGURA - 4)[:5]:
        print("  " + parte)

    print()
    if item["elenco"]:
        print("  Elenco: " + ", ".join(item["elenco"]))
    if item["extra"]:
        print("  " + (item.get("extra_rotulo") or "Obs") + ": " + item["extra"])
    if item["link"]:
        print("  Link:   " + item["link"])

    print()
    linha()
    print("  Compatibilidade: " + str(int(pontos)) + "/100")
    if motivos:
        for parte in textwrap.wrap("Por que: " + "; ".join(motivos), width=LARGURA - 4):
            print("  " + parte)
    linha()


def animar_roleta(candidatos):
    amostra = random.sample(candidatos, min(12, len(candidatos)))
    print()
    for item in amostra:
        texto = "  sorteando... " + item["titulo"][:45]
        print(texto.ljust(LARGURA) + "\r", end="", flush=True)
        time.sleep(0.09)
    print(" " * LARGURA + "\r", end="")


def filtrar(lista, dados_perfil, tipo, tempo, generos_alvo, nota_minima):
    aprovados = []

    for item in lista:
        if perfil.ja_assistiu(dados_perfil, item["titulo"]):
            continue
        if tipo != "ambos" and item["tipo"] != tipo:
            continue
        if tempo and item["duracao"] and item["duracao"] > tempo:
            continue
        if nota_minima and (item["nota"] or 0) < nota_minima:
            continue
        if generos_alvo and not set(item["generos"]) & set(generos_alvo):
            continue
        aprovados.append(item)

    return aprovados


def pontuar(item, tempo, generos_alvo):
    pontos = 0.0
    motivos = []

    if item["nota"]:
        pontos += item["nota"] * 5
        if item["nota"] >= 8:
            motivos.append("nota alta (" + str(item["nota"]) + ")")
    else:
        pontos += 25

    if tempo and item["duracao"]:
        aproveitamento = min(item["duracao"] / tempo, 1.0)
        pontos += 30 * aproveitamento
        if aproveitamento >= 0.7:
            motivos.append("encaixa bem nos seus " + str(tempo) + " min")

    if generos_alvo:
        acertos = len(set(item["generos"]) & set(generos_alvo))
        if acertos:
            pontos += min(20, 20 * acertos)
            motivos.append("e do genero que voce pediu")

    return min(pontos, 100.0), motivos


def sortear(aprovados, tempo, generos_alvo):
    ranking = sorted(
        ((pontuar(i, tempo, generos_alvo), i) for i in aprovados),
        key=lambda par: par[0][0],
        reverse=True,
    )
    finalistas = ranking[:10]
    pesos = [par[0][0] for par in finalistas]
    escolhido = random.choices(finalistas, weights=pesos, k=1)[0]

    (pontos, motivos), item = escolhido
    return item, pontos, motivos


def perguntar(pergunta, padrao=""):
    sufixo = " [" + padrao + "]" if padrao else ""
    resposta = input("  " + pergunta + sufixo + ": ").strip()
    return resposta or padrao


def modo_guiado():
    titulo_secao("O QUE ASSISTIR HOJE?")
    print()

    tipo = catalogo.sem_acento(perguntar("Filme, serie ou ambos?", "ambos"))
    if tipo not in ("filme", "serie", "ambos"):
        tipo = "ambos"

    bruto_tempo = perguntar("Quantos minutos livres voce tem?", "120")
    try:
        tempo = int("".join(c for c in bruto_tempo if c.isdigit()))
    except ValueError:
        tempo = 120

    print()
    print("  Generos: " + ", ".join(catalogo.generos_disponiveis()))
    genero = perguntar("Genero (vazio = qualquer)", "")

    bruto_nota = perguntar("Nota minima de 0 a 10", "7")
    try:
        nota_minima = float(bruto_nota.replace(",", "."))
    except ValueError:
        nota_minima = 7.0

    return tipo, tempo, genero, nota_minima


def mostrar_watchlist():
    dados = perfil.carregar()
    titulo_secao("SALVOS PARA DEPOIS")

    if not dados["watchlist"]:
        print("\n  Nada salvo ainda. Rode o programa e aperte [s] numa sugestao.\n")
        return

    print()
    for posicao, salvo in enumerate(dados["watchlist"], start=1):
        nota = str(salvo["nota"]) if salvo["nota"] else "-"
        duracao = str(salvo["duracao"]) + " min" if salvo["duracao"] else "n/d"
        print("  " + str(posicao) + ". " + salvo["titulo"] + " (" + salvo["ano"] + ")")
        print("     " + salvo["tipo"] + " | nota " + nota + " | " + duracao
              + " | salvo em " + salvo["salvo_em"])
    print()


def mostrar_vistos():
    dados = perfil.carregar()
    titulo_secao("JA ASSISTIDOS")
    print()
    if not dados["vistos"]:
        print("  Nenhum titulo marcado como visto ainda.\n")
        return
    for visto in dados["vistos"]:
        print("  - " + visto)
    print("\n  Total: " + str(len(dados["vistos"])) + " titulo(s) fora do sorteio.\n")


def montar_argumentos():
    analisador = argparse.ArgumentParser(
        description="Sugere o que assistir hoje com base no seu tempo livre.",
    )
    analisador.add_argument("--tipo", choices=["filme", "serie", "ambos"],
                            help="o que voce quer assistir")
    analisador.add_argument("--tempo", type=int, metavar="MIN",
                            help="minutos livres que voce tem")
    analisador.add_argument("--genero", help="genero desejado (ex: comedia, terror)")
    analisador.add_argument("--nota", type=float, help="nota minima de 0 a 10")
    analisador.add_argument("--watchlist", action="store_true",
                            help="lista o que foi salvo para depois e sai")
    analisador.add_argument("--vistos", action="store_true",
                            help="lista os titulos ja assistidos e sai")
    analisador.add_argument("--limpar-cache", action="store_true",
                            help="forca uma nova consulta as APIs")
    return analisador.parse_args()


def main():
    argumentos = montar_argumentos()

    if argumentos.watchlist:
        return mostrar_watchlist()
    if argumentos.vistos:
        return mostrar_vistos()
    if argumentos.limpar_cache:
        print("[cache] " + ("limpo." if catalogo.limpar_cache() else "nada para limpar."))

    usou_argumentos = any([argumentos.tipo, argumentos.tempo,
                           argumentos.genero, argumentos.nota])
    if usou_argumentos:
        tipo = argumentos.tipo or "ambos"
        tempo = argumentos.tempo or 0
        genero = argumentos.genero or ""
        nota_minima = argumentos.nota or 0.0
    else:
        tipo, tempo, genero, nota_minima = modo_guiado()

    generos_alvo = []
    if genero:
        generos_alvo = catalogo.traduzir_genero(genero) or []
        if not generos_alvo:
            print("\n  [aviso] Genero \"" + genero + "\" nao reconhecido - ignorando.")
            print("  Validos: " + ", ".join(catalogo.generos_disponiveis()))

    print()
    try:
        lista = catalogo.montar_catalogo(
            tipo, genero_api=generos_alvo[0] if generos_alvo else None
        )
    except requests.RequestException as erro:
        print("\n  [erro] Nao foi possivel falar com as APIs: " + str(erro))
        print("  Verifique sua conexao e tente de novo.\n")
        return

    dados_perfil = perfil.carregar()
    aprovados = filtrar(lista, dados_perfil, tipo, tempo, generos_alvo, nota_minima)

    print("[filtro] " + str(len(aprovados)) + " de " + str(len(lista))
          + " titulos passaram nos seus criterios.")

    if not aprovados:
        print("\n  Nenhum titulo bateu com os filtros. Tente afrouxar a nota")
        print("  minima, aumentar o tempo livre ou trocar o genero.\n")
        return

    while True:
        animar_roleta(aprovados)
        item, pontos, motivos = sortear(aprovados, tempo, generos_alvo)
        exibir_cartao(item, pontos, motivos)

        print()
        print("  [Enter] sortear outro   [v] ja vi esse   [s] salvar p/ depois   [q] sair")
        escolha = input("  > ").strip().lower()

        if escolha == "q":
            print("\n  Bom filme!\n")
            return

        if escolha == "v":
            perfil.marcar_visto(item["titulo"])
            aprovados = [i for i in aprovados if i["titulo"] != item["titulo"]]
            print("  [ok] \"" + item["titulo"] + "\" marcado como visto.")

        elif escolha == "s":
            if perfil.salvar_para_depois(item):
                print("  [ok] \"" + item["titulo"] + "\" salvo na sua watchlist.")
            else:
                print("  [info] Esse titulo ja estava na watchlist.")

        if not aprovados:
            print("\n  Acabaram os titulos que batem com os filtros.\n")
            return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Cancelado.\n")
        sys.exit(0)
