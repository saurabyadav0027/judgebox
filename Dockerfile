FROM python:3.12-slim

# Run as a non-root user so submitted code cannot modify the system.
RUN useradd --create-home judge
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY judgebox ./judgebox
USER judge

EXPOSE 8000
CMD ["uvicorn", "judgebox.api:app", "--host", "0.0.0.0", "--port", "8000"]
