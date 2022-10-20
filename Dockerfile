FROM python:3.10-alpine
WORKDIR /usr/src/app

RUN pip install --upgrade pip
# устанавливаем зависимости
COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

# копируем содержимое текущей папки в контейнер
COPY . /usr/src/app/

CMD ["python", "-u", "./main.py"]