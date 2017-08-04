new_site
========

Getting Started
---------------

- Change directory into your newly created project.

    cd new_site

- Create a Python virtual environment.

    python3 -m venv env

(Note for Windows Users: env/bin = env/Scripts)

- Upgrade packaging tools.

    env/bin/pip install --upgrade pip setuptools

- Install the project in editable mode with its testing requirements.

    env/bin/pip install -e ".[testing]"

- Initialize DataBase

    env/bin/initialize_new_site_db development.ini

- Run your project's tests.

    env/bin/pytest

- Enter the project environment

    source env/bin/activate

- Run the project.

    sh start.sh
