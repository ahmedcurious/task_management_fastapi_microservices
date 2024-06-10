FROM python:3.12-slim


# Define environment variables for Python and Poetry
ENV PYTHONDONTWRITEBYTECODE=1 \ 
    # Disable bytecode generation to prevent issues with the container's file system
    PYTHONUNBUFFERED=1 \
    # Unbuffer output to make debugging easier
    PYTHONFAULTHANDLER=1 \
    # Set Python's fault handler to crash on errors, ensuring that the container doesn't continue running if something goes wrong.
    PYTHONHASHSEED=random \
    # Set a random hash seed for Python's random module, which can help with reproducibility.
    PIP_NO_CACHE_DIR=off \ 
    # Disable pip's cache directory to force reinstallation of dependencies when building the image.
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    # Disable pip's version check to ensure that dependencies are installed regardless of their compatibility with our Python version.
    PIP_DEFAULT_TIMEOUT=100 \
    # Set a default timeout for pip operations, which can help prevent long-running installs from blocking the build process.
    POETRY_NO_INTERACTION=1 \
    # Set POETRY_NO_INTERACTION to prevent Poetry from prompting the user for input.
    POETRY_VIRTUALENVS_CREATE=false \
    # Create a new virtual environment when running 'poetry init'.
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    # Set the cache directory for Poetry to /tmp/poetry_cache.
    POETRY_HOME='/usr/local'  \
    # Set the Poetry home directory to /opt/poetry.
    POETRY_VERSION=1.8.2
# Specify the version of Poetry to use.

WORKDIR /app

# Install system dependencies required for potential Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.8.2

COPY pyproject.toml poetry.lock ./

COPY . /app/

RUN poetry install

EXPOSE 8000

CMD [ "poetry", "run", "uvicorn", "fastapi_backend.main:app", "--host", "0.0.0.0", "--reload" ]
