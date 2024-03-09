# Verwenden eines offiziellen Python Laufzeit-Images als Eltern-Image
FROM python:3.11-slim

# Setzen des Arbeitsverzeichnisses im Container
WORKDIR /app

# Kopieren der Anforderungsdatei in das Arbeitsverzeichnis
COPY requirements.txt ./

# Installieren von Abhängigkeiten aus der Anforderungsdatei
RUN pip install --no-cache-dir -r requirements.txt

# Kopieren des Projektinhalts in das Arbeitsverzeichnis
COPY . .

# Befehl, der beim Start des Containers ausgeführt wird
CMD ["python", "./app.py"]

