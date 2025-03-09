FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000
EXPOSE 8080

CMD ["python", "main.py"]
