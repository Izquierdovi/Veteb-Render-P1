# Imagen base ligera
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar todo el proyecto a la imagen
COPY Flask/ /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Precargar el modelo para que no se descargue en producción
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Puerto en el que correrá Gunicorn
EXPOSE 10000

# Comando para lanzar Flask con Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
