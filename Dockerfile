FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --progress-bar off --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

CMD python -m agent_tool
