chroma-ai/                       # корень репозитория
├── pyproject.toml               # зависимости, сборка, lint, форматирование
├── setup.cfg                    # конфигурация flake8, isort и т.д.
├── README.md                    # обзор проекта, быстрый старт
├── .gitignore
│
├── docs/                        # документация
│
├── scripts/                     # вспомогательные скрипты
│   ├── build_installer.sh       # собирает exe/AppImage/DMG
│   ├── run_local.sh             # запускает локальный сервер + туннель
│   └── ci_pipeline.sh           # пример шагов для GitHub Actions
│
├── assets/                      # статические артефакты
│   └── cloudflared/             # сюда кладём бинарники cloudflared.exe/.bin
│       ├── linux-amd64
│       ├── windows-amd64.exe
│       └── macos-amd64
│
├── src/                         # исходники
│   └── chroma_ai/               # основная библиотека/приложение
│       ├── __init__.py
│       ├── config.py            # загрузка и валидация конфига (pydantic)
│       ├── logging_config.py    # единые настройки логгирования
│       ├── main.py              # точка входа (CLI, argparse/typer)
│       │
│       ├── server/              # локальный WebSocket-сервер
│       │   ├── __init__.py
│       │   ├── ws_server.py      # старует FastAPI/WebSocket endpoint
│       │   └── handlers.py       # разделение логики обработки команд
│       │
│       ├── tunnel/              # служба управления облачным туннелем
│       │   ├── __init__.py
│       │   └── cloudflared.py    # класс TunnelManager: старт/стоп, парсинг URL
│       │
│       ├── webui/               # встроенный Web-UI (React/Next.js или Flask-templates)
│       │   ├── frontend/         # если Next.js — здесь весь проект JS
│       │   └── backend.py        # proxy-роуты → перенаправляют команды в ws_server
│       │
│       └── utils/               # вспомогательные модули
│           ├── __init__.py
│           ├── subprocesser.py   # обёртка над Popen с авто-рестартом
│           └── validator.py      # общие проверки, схемы
│
└── tests/                       # тесты
