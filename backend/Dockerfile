FROM python:3.11.4-slim

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install gunicorn==20.1.0 

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["python", "manage.py", "runserver", "0:8000"] 
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi.application"]
