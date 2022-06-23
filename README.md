# fastApiTestProject
## Запуск

Чтобы запустить проект, скопируйте текущий репозиторий и запустите следующие команды:

```cmd
sudo make build run
```

```cmd
sudo make init_and_migrate 
```

## Структура проекта

- `docker-compose.yml` - файл для запуска проекта в Docker-контейнерах (сервер и БД)
- `Dockerfile` - файл для создания Docker-контейнера сервера 
- `alembic.ini` - файл настройки Alembic
- `init_alembic.py` - файл инициализации Alembic 
- `Makefile` - для быстрого запуска заданных макросов
- `alembic_env.py` - стандартный файл для Alembic
- `requirements.txt` - файл со всеми Python-зависимостями
- `app`
  - `main.py` - основной файл (сервер)
  - `schemas.py` - файл со всеми схемами
  - `service.py` - файл для работы с логикой программы 
  - `db`
    - `db.py` - файл для работы с БД
    - `models.py` - файл с моделями из БД