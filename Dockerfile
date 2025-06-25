FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
ENV PYTHONPATH="/app:$PYTHONPATH"
CMD ["python", "-m", "cat_weather.main"]
