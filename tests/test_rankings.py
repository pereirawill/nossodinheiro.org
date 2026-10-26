"""Testes do ETL de rankings: montagem da posição e leitor mínimo de xlsx (sem rede)."""
import io, zipfile

from etl.rankings.extract import montar, _xlsx_rows


def test_montar_posicoes():
    nomes = {"BRA": "Brasil", "ARG": "Argentina", "CHL": "Chile"}
    linhas = [{"iso3": "BRA", "valor": 20.0, "ano": 2023}, {"iso3": "ARG", "valor": 5.0, "ano": 2022},
              {"iso3": "CHL", "valor": 4.0, "ano": 2023}, {"iso3": "WLD", "valor": 1.0, "ano": 2023}]  # agregado fica fora
    i = montar("homicidios", "Homicídios", "", "BM", "organismo oficial", "", "por 100 mil", False, linhas, nomes, {})
    assert [p["iso3"] for p in i["paises"]] == ["CHL", "ARG", "BRA"]      # menor é melhor
    assert i["brasil"] == {"posicao": 3, "valor": 20.0, "ano": 2023, "total": 3}
    assert i["anos_misturados"] is True and i["ano_referencia"] == 2023
    j = montar("pib", "PIB", "", "BM", "organismo oficial", "", "US$", True, linhas[:3], nomes, {})
    assert j["paises"][0]["iso3"] == "BRA" and j["brasil"]["posicao"] == 1
    # posição oficial prevalece quando a fonte a publica
    k = montar("idh", "IDH", "", "PNUD", "organismo oficial", "", "", True,
               [{"iso3": "BRA", "valor": 0.786, "ano": 2023, "posicao_oficial": 84}], nomes, {})
    assert k["brasil"]["posicao"] == 84


def _xlsx(strings, rows):
    """Monta um xlsx mínimo: rows = lista de listas; str vira sharedString, número vira <v>."""
    ss = "".join(f"<si><t>{s}</t></si>" for s in strings)
    cells = []
    for r, row in enumerate(rows, 1):
        cs = []
        for c, v in enumerate(row):
            ref = f"{chr(65 + c)}{r}"
            cs.append(f'<c r="{ref}" t="s"><v>{strings.index(v)}</v></c>' if isinstance(v, str) else f'<c r="{ref}"><v>{v}</v></c>')
        cells.append(f"<row r=\"{r}\">{''.join(cs)}</row>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/sharedStrings.xml", f"<sst>{ss}</sst>")
        z.writestr("xl/worksheets/sheet1.xml", f"<worksheet><sheetData>{''.join(cells)}</sheetData></worksheet>")
    return buf.getvalue()


def test_xlsx_rows():
    strings = ["Country / Territory", "ISO3", "CPI 2025 score", "Rank", "Denmark", "DNK", "Brazil", "BRA"]
    conteudo = _xlsx(strings, [["Country / Territory", "ISO3", "CPI 2025 score", "Rank"], ["Denmark", "DNK", 89, 1], ["Brazil", "BRA", 35, 107]])
    linhas = _xlsx_rows(conteudo)
    assert linhas[0] == ["Country / Territory", "ISO3", "CPI 2025 score", "Rank"]
    assert linhas[2] == ["Brazil", "BRA", 35.0, 107.0]
