# nossodinheiro.org
Nosso Dinheiro — painéis de transparência pública do Brasil com dados oficiais (Câmara, Portal da Transparência, Receita, TCU): quanto custa um deputado, emendas, Judiciário e Poderes. ETL em Python/DuckDB no GitHub Actions, site estático em Astro. Metodologia aberta.

Base para o perfil de Instagram sobre política e cidadania.

**Painéis:** 1) custo por deputado federal ✅ MVP · 1b) emendas parlamentares 🔧 ETL · 5) custo dos Poderes 🔧 ETL ·
2) orçamento por função · 3) arrecadação por estado · 4) obras paralisadas.

## Arquitetura
```
API/CSV oficiais ──► etl/ (Python + httpx) ──► data/raw (jsonl.gz)
                                                  │ DuckDB
                                                  ▼
                               data/parquet (artefato) + data/public/*.json (git)
                                                  │
                     site/ (Astro, SVG em build) ◄┘ ──► Cloudflare Pages
```
- ETL roda no GitHub Actions toda segunda (`.github/workflows/etl.yml`) e commita só o JSON agregado.
- O site é 100% estático; Cloudflare Pages faz o build (`cd site && npm run build`, saída `site/dist`) a cada push.
- PNGs 1080×1350 para Instagram saem em `data/public/`.

## Rodar local
```
pip install -r requirements.txt
make test            # smoke test com fixtures sintéticas
make etl ANO=2026    # ou FONTE=bulk para o CSV anual (muito mais rápido p/ anos fechados)
make site            # build do Astro em site/dist
```

## Deploy (GitHub Actions → Cloudflare Pages)
Tudo roda no Actions: `etl.yml` (semanal, ou a cada push em `etl/`) commita os JSONs e
dispara `deploy.yml`, que builda o Astro e publica com `wrangler pages deploy`.

Setup único:
1. Cloudflare → Workers & Pages → Create → Pages → **Upload assets** (Direct Upload), nome do projeto `nossodinheiro`.
2. Cloudflare → My Profile → API Tokens → Create → template **"Edit Cloudflare Workers"** (inclui Pages) → copie o token.
3. GitHub → Settings → Secrets and variables → Actions: `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID` (Account ID fica na home do dashboard, lado direito).
4. GitHub → Settings → Actions → General → Workflow permissions: **Read and write**.
5. Actions → "ETL Câmara" → Run workflow. Ao terminar, o deploy roda sozinho.
6. Pages → projeto `nossodinheiro` → Custom domains → `nossodinheiro.org`.

Metodologia: `docs/metodologia/painel-1-custo-deputados.md`.

## Licença
- **Código** (`etl/`, `site/`, workflows): [MIT](LICENSE).
- **Dados agregados, textos e gráficos** (`data/public/`, `docs/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br) — use e republique com crédito a *Nosso Dinheiro (nossodinheiro.org)*.
- Os dados brutos são públicos por força da Lei de Acesso à Informação; a licença acima cobre apenas a transformação e a apresentação feitas aqui.
