FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# O Hugging Face Spaces usa por padrão a porta 7860
CMD ["uvicorn", "app.py:app", "--host", "0.0.0.0", "--port", "7860"]