# fastApiTestProject
##
Сервер работает на веб-фреймворке Python FastAPI и uvicorn. В качестве БД используется
PostgreSQL, Alembic для миграций. База данных находится в одном Docker-контейнере, сервер - 
в другом. Для быстрого запуска используются команды из `Makefile`.

## Запуск

Чтобы запустить проект, скопируйте текущий репозиторий и запустите следующие команды:

```cmd
sudo make build run
```

```cmd
sudo make init_and_migrate 
```

Для остановки используйте:
```cmd
sudo make stop 
```

Для удаления контейнера:
```cmd
sudo make destroy 
```

## Структура проекта

- `docker-compose.yml` - файл для запуска проекта в Docker-контейнерах (сервер и БД)
- `Dockerfile` - файл для создания Docker-контейнера сервера 
- `alembic.ini` - файл настройки Alembic
- `init_alembic.py` - файл инициализации Alembic 
- `Makefile` - для быстрого запуска заданных макросов
- `alembic_env.py` - стандартный файл для Alembic
- `requirements.txt` - файл со всеми Python-зависимостями
- `pgdata` - volume Docker-контейнера с PostgreSQL, где хранится данные БД
- `app`
  - `main.py` - основной файл (сервер)
  - `schemas.py` - файл со всеми для валидации
  - `service.py` - файл для работы с логикой программы 
  - `db`
    - `db.py` - файл для работы с БД
    - `models.py` - файл с моделями из БД