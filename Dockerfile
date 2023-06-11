FROM python:3.10-alpine as development

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN ln -sf /usr/share/zoneinfo/Europe/Warsaw /etc/timezone && \
    ln -sf /usr/share/zoneinfo/Europe/Warsaw /etc/localtime


RUN pip install --upgrade pip --no-cache-dir
RUN apk update

COPY Pipfile Pipfile.lock ./
COPY game/entrypoint.sh /entrypoint.sh

RUN apk add --update --no-cache postgresql-client jpeg-dev
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    && apk add libpq-dev gcc \
    && apk add libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev python3-dev

RUN pip install pipenv
RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile
RUN pipenv install -d --system --deploy --ignore-pipfile
RUN pipenv install psycopg2

RUN apk del .tmp-build-deps

WORKDIR /core
COPY . .
WORKDIR /core/game

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]


FROM development as prod
RUN adduser -u 5678 --disabled-password --gecos "" user && chown -R user /core/game
USER user


ENTRYPOINT [ "python" ]
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--log-level", "info", "app:app"]
