# Le contexte de build est la racine du projet (voir docker-compose.yml),
# pour pouvoir copier à la fois api/ et database/.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Les dépendances d'abord : cette couche est réutilisée tant que
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Le code de l'API et le fichier de données.
COPY api ./api
COPY database ./database

EXPOSE 8000

# --host 0.0.0.0 est obligatoire pour que le port soit accessible
# depuis Windows via le mapping de docker-compose.
## savoir --> définir le mapping
CMD ["uvicorn", "api.api:app", "--host", "0.0.0.0", "--port", "8000"]