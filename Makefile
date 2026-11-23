# MOCK=1 make demo-c  -> прогон на заскриптованной модели, без ключа
ENV_FILE := $(if $(MOCK),.env.mock,.env)
PROFILES := $(if $(MOCK),--profile mock,)
N := docker compose --progress quiet -f compose.naive.yaml --env-file $(ENV_FILE) $(PROFILES)
S := docker compose --progress quiet -f compose.secure.yaml --env-file $(ENV_FILE) $(PROFILES)
RUNS ?= 10

.PHONY: warm build up-naive up-secure demo-a demo-c demo-d watch-c watch-d audit diff test-c test-d record-a record-c record-d down

# up собирает образы, только если их ещё нет: посреди демо ничего не пересобирается и не пересоздаётся.
up-naive:
	@$(N) up -d --wait --quiet-pull >/dev/null
up-secure:
	@$(S) up -d --wait --quiet-pull >/dev/null
build:             ## пересобрать образы после правок в services/ или egress-proxy/
	@$(N) build -q >/dev/null && $(S) build -q >/dev/null
	@$(MAKE) -s down   # иначе gateway держит в DNS-кэше адрес пересозданного контейнера

warm:              ## загрузить локальную модель Ollama в память и держать её 2 часа
	@ollama run "$$(grep '^LLM_MODEL=' $(ENV_FILE) | cut -d= -f2)" --keepalive 2h "Ответь одним словом: готов"

demo-a: up-naive  ## Сценарий A: обычный тикет
	@$(N) run --rm agent --ticket T-1041

demo-c: up-naive  ## Сценарий C: атака на naive (во втором окне: make watch-c)
	@$(N) run --rm agent --ticket T-1042

demo-d: up-secure ## Сценарий D: та же атака на secure (во втором окне: make watch-d)
	@TOKEN=$$($(S) exec -T tools python tools_server.py mint T-1042) && \
	  $(S) run --rm -e TOOLS_TOKEN=$$TOKEN agent --ticket T-1042
	@$(MAKE) -s audit

watch-c:           ## сервер атакующего
	@$(N) logs -f --no-log-prefix collector
watch-d:           ## egress proxy + audit log инструментов + сервер атакующего
	@$(S) logs -f egress-proxy tools collector

audit:
	@printf "\n\033[1;35m── audit log инструментов ──\033[0m\n"; $(S) exec -T tools tail -n 6 /tmp/tools-audit.jsonl
	@printf "\n\033[1;35m── egress proxy ──\033[0m\n"; $(S) exec -T egress-proxy tail -n 4 /var/log/squid/access.log

diff:              ## что отличается между профилями (код агента одинаковый)
	@git diff --no-index --color=always compose.naive.yaml compose.secure.yaml || true

test-c: up-naive  ## атака должна пройти RUNS из RUNS
	@COMPOSE="$(N)" scripts/repeat.sh c $(RUNS)
test-d: up-secure ## атака должна блокироваться RUNS из RUNS
	@COMPOSE="$(S)" scripts/repeat.sh d $(RUNS)

record-%:          ## fallback-запись: make record-a / record-c / record-d
	@mkdir -p recordings && asciinema rec --overwrite -c "make -s demo-$*" recordings/demo-$*.cast

down:
	@$(N) --profile run --profile mock down -v --remove-orphans
	@$(S) --profile run --profile mock down -v --remove-orphans
