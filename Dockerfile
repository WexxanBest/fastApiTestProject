FROM python:3.8

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

COPY ./alembic.ini /code/alembic.ini
COPY ./alembic_env.py /code/alembic_env.py
COPY ./init_alembic.py /code/init_alembic.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
