# Сценарий B: сценарий записи (2 минуты после монтажа)

В кадре должны быть три момента: YAML задачи, выбор инфраструктуры оптимизатором, готовый endpoint.
Ожидание provisioning и `setup` ускорить при монтаже.

## Подготовка
1. `sky check`: облако, в котором будет запись, в статусе enabled.
2. Терминал: шрифт 20+, ширина ~110 колонок, тёмная тема, промпт короткий (`$ `).
3. `export KEY=$(openssl rand -hex 16)`.

## Дубль
| # | Что в кадре | Команда | Что сказать за кадром |
|---|---|---|---|
| 1 | YAML задачи | `bat skypilot/vllm.yaml` | «Описываю, что нужно, а не где: любой из трёх GPU, порт, команда запуска» |
| 2 | Оптимизатор | `sky launch -c lecture-llm skypilot/vllm.yaml --env VLLM_API_KEY=$KEY -i 30 --down` | Задержаться на таблице выбора: регион, тип GPU, цена. Подтвердить `Y` |
| 3 | Provisioning и setup | (ускорить x8–x16) | «Autostop через 30 минут простоя, после остановки кластер удаляется» |
| 4 | Endpoint | `sky status --endpoint 8000 lecture-llm` | «Endpoint OpenAI-совместимый, агенту всё равно, что за ним» |
| 5 | Переключение агента | `LLM_BASE_URL=http://<endpoint>/v1 LLM_MODEL=Qwen/Qwen2.5-7B-Instruct LLM_API_KEY=$KEY make demo-a` | «Код агента не менялся, поменялась одна переменная» |

## После записи
`sky down lecture-llm -y` и `sky status` пустой. Autostop с `--down` страхует, если забыть.

## Проверить перед записью
- актуальность флагов `-i/--idle-minutes-to-autostop`, `--down`, `sky status --endpoint`;
- версию vLLM и парсер tool calling для выбранной модели;
- открытый порт 8000 защищён только `--api-key`: на время записи достаточно, в проде endpoint за gateway.
