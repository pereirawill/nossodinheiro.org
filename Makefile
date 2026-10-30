ANO ?= 2026
FONTE ?= bulk

etl: ## extrai + transforma + gráfico
	python -m etl.camara.extract deputados
	@if [ "$(FONTE)" = "bulk" ]; then python -m etl.camara.extract ceap-bulk --ano $(ANO); \
	else python -m etl.camara.extract despesas --ano $(ANO); fi
	python -m etl.camara.transform --ano $(ANO) --fonte $(FONTE)
	python -m etl.camara.chart --ano $(ANO) --top 20 --por deputado
	python -m etl.camara.chart --ano $(ANO) --top 20 --por partido
	cp data/public/*.json site/public/data/

checar: ## checagem mecânica do site (glossário, links, datasets, JSONs, workflows) — sem modelo, custo zero
	python tools/checar_site.py
.PHONY: checar

test:
	python -m pytest tests/ -q

site:
	cd site && npm install && npm run build
.PHONY: etl test site

senado: ## senadores: lista + recursos utilizados + transform
	python -m etl.senado.extract senadores
	python -m etl.senado.extract recursos --ano $(ANO)
	python -m etl.senado.transform --ano $(ANO)
	cp data/public/custo_senador_*.json data/public/meta_senado_*.json site/public/data/

stf: ## ministros do STF: folha (ministros + gabinetes) + transform. Se o Actions levar 403, rode aqui.
	python -m etl.stf.extract folha --ano $(ANO)
	python -m etl.stf.transform --ano $(ANO)
	cp data/public/custo_ministro_stf_*.json data/public/meta_stf_*.json site/public/data/
.PHONY: senado stf

carga-mundo: ## carga tributária por país (OCDE, governo geral com previdência)
	python -m etl.carga_mundo.extract
	cp data/public/carga_mundo.json site/public/data/
.PHONY: carga-mundo

industria: ## indústria: participação (Banco Mundial) e produção física (IBGE PIM-PF)
	python -m etl.industria.extract
	cp data/public/industria.json site/public/data/
.PHONY: industria

precos: ## poder de compra: combustível (ANP) em minutos de trabalho e nível de preços (ICP)
	python -m etl.precos.extract
	cp data/public/precos.json site/public/data/
.PHONY: precos

economia: ## economia: PIB (IBGE), Selic (BCB) e resultado do governo (Tesouro)
	python -m etl.economia.extract
	cp data/public/economia.json site/public/data/
.PHONY: economia

desenvolvimento: ## desenvolvimento por estado: Censos (educação) e ODS 16.1.1 (homicídios)
	python -m etl.desenvolvimento.extract
	cp data/public/desenvolvimento.json site/public/data/
.PHONY: desenvolvimento

transito: ## mortes no trânsito: ODS 3.6.1 (SIM/Ministério da Saúde) pelo SIDRA
	python -m etl.transito.extract
	cp data/public/transito.json site/public/data/
.PHONY: transito

divida: ## dívida: juros nominais (RTN) e estoque da DPF (Tesouro Transparente)
	python -m etl.divida.extract
	cp data/public/divida.json site/public/data/
.PHONY: divida

fotos: ## baixa as fotos oficiais que faltam (Câmara e Senado) para site/public/fotos
	python -m etl.fotos.baixar
.PHONY: fotos

saneamento: ## saneamento: Censo (1991-2022) e PNAD Contínua, pelo SIDRA
	python -m etl.saneamento.extract
	cp data/public/saneamento.json site/public/data/
.PHONY: saneamento

bancos: ## lucro dos bancos: IF.data do Banco Central (cache em data/raw/ifdata) + conferência na CVM
	python -m etl.bancos.extract
	cp data/public/bancos.json site/public/data/
.PHONY: bancos

estatais: ## lucro das estatais: CVM (DFP + formulário de referência) + SEST + dividendos do Tesouro
	python -m etl.estatais.extract
	cp data/public/estatais.json site/public/data/
.PHONY: estatais

irpf: ## imposto de renda: planilha dos Grandes Números do IRPF (cache em data/raw)
	python -m etl.irpf.extract
	cp data/public/irpf.json site/public/data/
.PHONY: irpf

TRIBUNAL ?= stj
tribunais: ## folha de um tribunal superior (TRIBUNAL=stj|tst|stm): extract + transform
	python -m etl.tribunais.extract --tribunal $(TRIBUNAL) --ano $(ANO)
	python -m etl.tribunais.transform --tribunal $(TRIBUNAL) --ano $(ANO)
	cp data/public/custo_magistrado_$(TRIBUNAL)_*.json data/public/meta_$(TRIBUNAL)_*.json site/public/data/
.PHONY: tribunais

sugestoes: ## lê as sugestões enviadas no site (precisa de CLOUDFLARE_API_TOKEN com permissão de D1)
	npx --yes wrangler@4 d1 execute nossodinheiro-agora --remote -y --json \
	  --command "SELECT datetime(ts,'unixepoch','-3 hours') AS quando, texto, contato, pagina FROM sugestao ORDER BY ts DESC LIMIT 50"

agora-status: ## mostra o painel ao vivo como o site o vê
	curl -s https://nossodinheiro.org/api/agora | python -m json.tool
.PHONY: sugestoes agora-status
