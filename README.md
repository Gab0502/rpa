# O Que Assistir Hoje

Automação em Python que decide o que você vai assistir hoje à noite.

## O problema

Todo mundo já passou por isso: você tem uma hora e meia livre, abre o streaming
e gasta 40 minutos rolando o catálogo sem decidir nada. No fim, não assiste a
nada ou coloca algo que você já viu três vezes.

O problema real não é falta de opção — é **excesso** de opção sem filtro. Os
catálogos não sabem quanto tempo você tem agora, e não lembram o que você já viu.

## A solução

O script faz quatro perguntas (tipo, tempo livre, gênero e nota mínima), busca
o catálogo em duas APIs públicas, **descarta o que não cabe no seu tempo e o que
você já assistiu**, pontua cada título restante de 0 a 100 e sorteia uma
sugestão entre as mais compatíveis — mostrando o porquê da escolha.

Se não gostou, aperta Enter e ele sorteia outra. Se já viu, aperta `v` e aquele
título nunca mais aparece. Se gostou mas não é pra agora, aperta `s` e vai pra
sua watchlist.

## Tecnologias

| Recurso | Para quê |
|---|---|
| `requests` | Consumo das duas APIs REST |
| `BeautifulSoup` | Limpeza do HTML que vem dentro das sinopses |
| `argparse` | Interface de linha de comando |
| `json` + `pathlib` | Cache do catálogo e memória do usuário |
| `random.choices` | Sorteio ponderado pela pontuação |

### Integração externa (requisito do checkpoint)

Duas APIs REST públicas, **nenhuma exige cadastro ou chave de acesso**:

- **TVMaze** — `https://api.tvmaze.com/shows` → catálogo de séries
- **Cinemeta** — `https://v3-cinemeta.strem.io/catalog/movie/top` → catálogo de filmes

O `BeautifulSoup` entra porque a TVMaze devolve a sinopse **embrulhada em HTML**
(`<p>`, `<b>`, `<i>`). Jogar isso direto no terminal mostraria as tags na tela,
então o texto passa pelo parser antes de ser exibido.

## Instalação

```bash
py -m pip install -r requirements.txt
```

> No Windows, o comando é `py`. Se no seu PC o `python` estiver no PATH, use
> `python` no lugar de `py` em todos os comandos abaixo.

## Como usar

**Modo guiado** (ele faz as perguntas):

```bash
py assistir.py
```

**Modo direto** (já com os filtros):

```bash
py assistir.py --tipo filme --tempo 120 --genero comedia --nota 7
py assistir.py --tipo serie --tempo 45 --nota 8
```

**Consultas:**

```bash
py assistir.py --watchlist      # o que você salvou pra depois
py assistir.py --vistos         # o que já marcou como assistido
py assistir.py --limpar-cache   # força nova consulta às APIs
```

### Argumentos

| Argumento | Descrição |
|---|---|
| `--tipo` | `filme`, `serie` ou `ambos` |
| `--tempo MIN` | minutos livres que você tem |
| `--genero` | em português: `comedia`, `terror`, `acao`, `ficcao`, `drama`... |
| `--nota` | nota mínima de 0 a 10 |

## Exemplo de saída

```
[rede] Consultando as APIs de filmes e series...
[rede] 50 titulos baixados.
[filtro] 32 de 50 titulos passaram nos seus criterios.

+========================================================================+
| SUGESTAO DE HOJE                                              [ FILME ]|
+========================================================================+

  Toy Story 3  (2010)
  Nota 8.3/10   |   103 min   |   Animation, Adventure, Comedy

  The toys are mistakenly delivered to a day-care center instead of
  the attic right before Andy leaves for college, and it's up to Woody
  to convince the other toys that they weren't abandoned and to return
  home.

  Elenco: Tom Hanks, Tim Allen, Joan Cusack
  Direcao: Lee Unkrich
  Link:   https://www.imdb.com/title/tt0435761/

+------------------------------------------------------------------------+
  Compatibilidade: 87/100
  Por que: nota alta (8.3); encaixa bem nos seus 120 min; e do genero
  que voce pediu
+------------------------------------------------------------------------+

  [Enter] sortear outro   [v] ja vi esse   [s] salvar p/ depois   [q] sair
```

## Como a pontuação funciona

Cada título recebe de 0 a 100 pontos somando três critérios:

| Critério | Peso | Lógica |
|---|---|---|
| Qualidade | até 50 | a nota do público multiplicada por 5 |
| Encaixe no tempo | até 30 | proporcional a quanto do seu tempo livre o título aproveita |
| Gênero | até 20 | bônus por gênero que bate com o pedido |

O detalhe do **encaixe no tempo** é o que dá "inteligência" ao sorteio: se você
reservou 2 horas, um episódio de 22 minutos pontua menos que um filme de 110,
mesmo que os dois caibam na janela.

E o sorteio não pega sempre o primeiro do ranking — ele separa os 10 melhores e
sorteia entre eles **usando a pontuação como peso**. Os melhores saem mais
vezes, mas a sugestão varia a cada execução.

## Estrutura dos arquivos

```
Gabriel/
├── assistir.py        # programa principal: CLI, perguntas, pontuação e sorteio
├── catalogo.py        # integração com as duas APIs + limpeza de HTML + cache
├── perfil.py          # memória local (vistos e watchlist) em JSON
├── requirements.txt
└── README.md
```

Arquivos gerados na primeira execução (não precisam ir no entregável):

- `cache_catalogo.json` — catálogo guardado por 12h para não bater na API toda hora
- `meu_perfil.json` — seus títulos vistos e sua watchlist

## Tratamento de erros

- **Sem internet / API fora do ar** → mensagem clara, sem stack trace
- **Gênero digitado errado** → avisa e lista os gêneros válidos, segue rodando
- **Cache corrompido** → descarta e busca de novo
- **Nenhum título bateu com os filtros** → sugere afrouxar os critérios
- **Ctrl+C** → sai limpo, sem despejar erro na tela
