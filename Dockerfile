FROM python:3.9-slim-buster
WORKDIR /app
COPY src/ .
# Install Flask from the requirements file
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
ENV PORT=8080
CMD ["python", "app.py"]
