# Usa una imagen base ligera de Python
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia solo el archivo de requisitos primero para aprovechar el caché de Docker
COPY ./requirements.txt /app/requirements.txt

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de tu backend al contenedor
COPY . /app

# El comando que se ejecuta cuando el contenedor inicia
# Inicia el servidor FastAPI
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]