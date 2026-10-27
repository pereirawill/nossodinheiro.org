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

irpf: ## imposto de renda: planilha dos Grandes Números do IRPF (cache em data/raw)
	python -m etl.irpf.extract
	cp data/public/irpf.json site/public/data/
.PHONY: irpf
