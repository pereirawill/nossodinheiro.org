"""
Constantes do Painel 1 — Custo por deputado federal.

Cada valor fixo carrega a fonte e a data de verificação. Mantenha isto em
sincronia com docs/metodologia/painel-1-custo-deputados.md. Nunca altere um
número aqui sem atualizar a metodologia.
"""

from __future__ import annotations

from datetime import date

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
# Arquivos anuais da CEAP (mais rápido que paginar a API para um ano inteiro).
CEAP_BULK_CSV = "https://www.camara.leg.br/cotas/Ano-{ano}.csv.zip"

LEGISLATURA_ATUAL = 57  # 2023-02-01 a 2027-01-31

# --- Subsídio (salário) -----------------------------------------------------
# Decreto Legislativo 172/2022 escalonou o subsídio em 4 parcelas anuais
# (fevereiro de cada ano). Valor bruto mensal, em R$.
# Fonte: Câmara dos Deputados / Gazeta SP (03/03/2026) / NSC Total (03/03/2026).
SUBSIDIO_MENSAL: list[tuple[date, float]] = [
    (date(2023, 2, 1), 39_293.32),
    (date(2024, 2, 1), 41_650.92),
    (date(2025, 2, 1), 44_008.52),
    (date(2026, 2, 1), 46_366.19),
]
# 13º subsídio + 1/3 de férias são pagos aos deputados (Lei 9.506/97 e atos da
# Mesa). Modelamos como 13 + 1/3 subsídios/ano. Marcado como premissa na
# metodologia até conferirmos a folha publicada na transparência da Câmara.
SUBSIDIOS_POR_ANO = 13 + 1 / 3


def subsidio_mensal_em(dt: date) -> float:
    valor = SUBSIDIO_MENSAL[0][1]
    for inicio, v in SUBSIDIO_MENSAL:
        if dt >= inicio:
            valor = v
    return valor


# --- Verba de gabinete ------------------------------------------------------
# Limite mensal para contratar até 25 secretários parlamentares.
# Fonte: camara.leg.br/transparencia/gastos-parlamentares (lido em 26/10/2026).
# Observação: o gasto REAL por gabinete não está na API de Dados Abertos; é
# publicado por deputado no site da Câmara. No MVP usamos o TETO (estimativa
# superior) e sinalizamos isso no gráfico.
VERBA_GABINETE_TETO_MENSAL = 165_806.07
VERBA_GABINETE_VERIFICADA_EM = date(2026, 10, 26)

# --- Auxílio-moradia --------------------------------------------------------
# Pago a quem não ocupa apartamento funcional. Fonte: idem acima.
AUXILIO_MORADIA_MENSAL = 4_253.00
# Nº de apartamentos funcionais (a Câmara informa 447 em 2026; artigos de
# março/2026 citam 432). Usamos o valor do site oficial.
APARTAMENTOS_FUNCIONAIS = 447
# Sem lista pública fácil de quem ocupa imóvel funcional, o MVP NÃO soma o
# auxílio-moradia ao custo individual; ele aparece como linha separada
# "estimativa máxima". Veja metodologia §3.4.
INCLUIR_AUXILIO_MORADIA_NO_TOTAL = False

# --- CEAP (cota parlamentar) ------------------------------------------------
# O gasto real vem da API/CSV. O TETO mensal varia por UF (Ato da Mesa 43/2009
# e atualizações); em 2026 vai de ~R$ 41,6 mil (DF) a ~R$ 57,3 mil (RR).
# A tabela completa por UF ainda precisa ser carregada de fonte primária —
# ver TODO em docs/metodologia. Só é usada para "% do teto", não para o custo.
CEAP_TETO_UF: dict[str, float] = {
    "DF": 41_600.00,  # aproximado, fonte secundária (mar/2026)
    "RR": 57_300.00,  # aproximado, fonte secundária (mar/2026)
}
