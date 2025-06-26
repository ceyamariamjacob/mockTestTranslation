# Use an official Python base image
FROM docker-master.cdaas.oraclecloud.com/docker-cxsales-dev/python:3.11.8

# Set working directory
WORKDIR /app

# Copy requirements.txt and pyproject.toml, then install Python dependencies
COPY requirements.txt langgraph.json .env intent.json Makefile reflection.py /app/
RUN pip install --upgrade pip --index-url=https://artifacthub-pypi.oci.oraclecorp.com/api/pypi/pypi-registry/simple --trusted-host=oraclecorp.com --no-cache-dir && \
    pip install -r requirements.txt --upgrade  --index-url=https://artifacthub-pypi.oci.oraclecorp.com/api/pypi/pypi-registry/simple --trusted-host=oraclecorp.com --no-cache-dir


# Command to run the LangGraph server or Python application
CMD ["langgraph", "dev", "--studio-url", "http://localhost:2024","--no-browser","--host","0.0.0.0", "--port","2024"]
