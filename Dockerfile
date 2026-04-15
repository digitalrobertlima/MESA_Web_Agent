FROM python:3.10-slim
WORKDIR /app
# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# Expor a porta que o HF exige
EXPOSE 7860
CMD ["uvicorn", "app.py:app", "--host", "0.0.0.0", "--port", "7860"]