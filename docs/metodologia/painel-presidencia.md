# Painel — Quanto gasta a Presidência da República

Última revisão: 2026-10-26. Código: `etl/presidencia/`. Atualização mensal (dia 15).

## 1. O que existe e o que não existe

Não há uma linha "gasto do presidente" publicada por nenhum órgão. O que o governo publica, e usamos:

| Bloco | Fonte | Como |
|---|---|---|
| Subsídio do presidente, vice e ministros de Estado | Decreto Legislativo 172/2022, art. 1º (R$ 46.366,19 desde 1º/fev/2025, igual ao dos parlamentares) | valor fixo em `beneficios.ts`/página |
| Cartão corporativo (CPGF) da Presidência | Portal da Transparência, download de dados `cpgf/AAAAMM` (ZIP com CSV, latin-1, `;`), sem chave | órgão superior 20000: Presidência (20101), Vice-Presidência (60000), Fundo de Imprensa Nacional (20116), EBC (20415) |
| Despesa paga pelos órgãos da Presidência | SIOP (painel Poderes), unidades orçamentárias do órgão 20000 | tabela reaproveitada de `poderes_orgaos_<ano>.json` |
| Viagens e diárias | Portal, download `viagens/AAAA` (ZIP anual ~90 MB) | **próximo bloco** (extrator pronto, página ainda não) |

"Primeira-dama" não é cargo nem centro de custo; não há dado com esse nome. O que houver está nas despesas acima.

## 2. Cartão corporativo: regras

- O mês é o **mês do extrato** (coluna MÊS EXTRATO), como o Portal organiza; a data da transação pode ser do mês anterior.
- **Sigiloso** = linha publicada como "Sigiloso" / "Informações protegidas por sigilo" (portador e fornecedor ocultos por
  segurança do presidente, vice e famílias; LAI art. 23). Mostramos o total sob sigilo e o percentual; em 2026 é ~98% do
  cartão da Presidência. Isso é o dado; não inferimos no que foi gasto.
- Tipos: "Sob sigilo", "Compra", "Compra no exterior" (transação `INT$`), "Saque em dinheiro" (`SAQUE…`).
- Total do governo = soma de todas as linhas do CSV do mês (todos os órgãos), para dar escala.
- Privacidade: CPF do portador já vem mascarado pelo Portal; CPF de favorecido pessoa física é mascarado no extrator
  (`***.xxx.xxx-**`); o site lista só favorecidos pessoa jurídica (CNPJ) e o número de portadores, não seus nomes.
- Meses ainda não publicados respondem HTTP 403 e são pulados; o painel informa quantos meses do ano há.

- **Tipo de serviço**: a parte identificada com CNPJ é classificada pela atividade principal (CNAE) que o fornecedor declara
  à Receita Federal, consultada por API pública (BrasilAPI; minhareceita.org de reserva) e guardada em `data/cnae_cache.json`.
  O mapa CNAE → rótulo está em `etl/presidencia/cnae.py` (ex.: 4731 = postos de combustível; 55 = hospedagem; 56 = alimentação).
  Nada é inferido pelo nome do fornecedor. 2026: 60% da parte identificada é combustível.

## 3. Resultado (lido em 2026-10-26)

2026, jan–ago: Presidência R$ 10,47 mi (98% sob sigilo; R$ 1,31 mi/mês); governo federal inteiro R$ 72,46 mi.
2025: Presidência R$ 23,13 mi (98% sob sigilo); governo R$ 122,25 mi. Parte identificada de 2026: R$ 224 mil, em
postos de combustível, material e tecnologia; 41 portadores identificados.

## 4. Pendências

1. Viagens e diárias da Presidência (ZIP anual já baixável; separar presidente/comitiva não é possível pela fonte,
   que identifica órgão e servidor, não "o presidente").
2. Série 2019–2026 do cartão para comparar governos (mesma fonte, basta rodar os anos).
3. Custo das equipes de ex-presidentes (dataset da Presidência, portal fora do ar em 26/10/2026).
