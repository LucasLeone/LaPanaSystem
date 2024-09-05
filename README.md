
# LaPanaSystem

**LaPanaSystem** is a comprehensive software solution designed to manage a bakery's daily operations. It includes features such as:

- **Retail and Wholesale Sales Panel**: Manage and track both retail and wholesale transactions.
- **Delivery Panel**: Coordinate and manage the distribution of products to customers.
- **Payment Panel**: Handle payment collections for sales.
- **Full CRUD Functionality**: Create, Read, Update, and Delete all relevant entities (products, customers, orders, etc.).

This project is part of the requirements for my intermediate degree in Information Systems Engineering and will be deployed at my family’s bakery for real-world use.

LaPanaSystem streamlines various processes, making the management of a bakery more efficient.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up the Project

To set up the project using Docker, run the following commands:

1. Build the Docker containers:
    ```bash
    docker compose -f docker-compose.local.yml build
    ```

2. Start the containers:
    ```bash
    docker compose -f docker-compose.local.yml up
    ```

### Setting Up Your Users

- To create a normal user, you need to have the `user_type` set as administrator or be a superuser. You can make a POST request to: `http://localhost:8000/api/v1/users/` 
with the appropriate user data.
- To create a **superuser account**, run this command:
    ```bash
    docker compose -f docker-compose.local.yml run --rm django python manage.py createsuperuser
    ```

#### Running tests with pytest

To run the tests using Docker, execute:

    ```
    docker compose -f docker-compose.local.yml run --rm django pytest
    ```
    
### Celery

This app comes with Celery.

To run a celery worker:

    ```
    cd lapanasystem
    celery -A config.celery_app worker -l info
    ```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

    ```
    cd lapanasystem
    celery -A config.celery_app beat
    ```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

    ```
    cd lapanasystem
    celery -A config.celery_app worker -B -l info
    ```
