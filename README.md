oc-lit-revu
===========

Openclassrooms Python Project 9

A community book reviewing app

**TABLE OF CONTENTS**

 - [Dependencies and requirements](#dependencies-and-requirements)
 - [Installation steps](#installation-steps)
 - [Run the app locally](#run-the-app-locally)
 - [Manage the app as superuser](#manage-the-app-as-superuser)
 - [Clear the database](#clear-the-database)
 - [Configuration, testing and debugging](#configuration-testing-and-debugging)


# Dependencies and requirements

This app requires [Python 3.10+](https://www.python.org/) and [Django 5.1](https://www.djangoproject.com/) (see installation notes below).

The app's database is powered by SQLite3 (shipped with Python by default).

# Installation Steps

## 1. Get the codebase and the Python environment

clone this repository:

    git clone git@github.com:christian-debray/oc-litrevu.git .

install a python virtual envirionment:

    python -m venv env

run the virtual environment:

    source env/bin/activate

install the required packages

    pip install -r requirements.txt


## 2. Install the database

### 2.1 Setup the database: initial migration

Check that the initial migration is already prepared:

    python manage.py showmigrations

 --> `0001_initial` should appear under the "app" section in the list of migrations.

If the initial migration is missing, try :

    python manage.py makemigrations app

Once the initial migration is ready:

    python manage.py migrate

### 2.2 Test and Check everything is fine

    python manage.py check

    python manage.py test

### 2.3 Optional: Load initial data from fixtures:

_**Note**: All models must be empty before loading fixtures. See also [Clear the database](#clear-the-database)_

If you wish to try the app with some pre-loaded data, you can load the fixtures provided in this repo:

load from YAML file (requires PyYAML):

    python manage.py loaddata --app app tests.yaml

or load from JSON (JSON format is always available but less human-readable)
    
    python manage.py loaddata --app app tests.json

#### 2.3.1 Available user accounts for testing:

  - Alix
  - Toto_23
  - ReviewService
  - ObservEr
  - Bob

These test users share the same password: `Ab1;mlkjhgfdsq`

### 2.4 Optional: new superuser account

You can create a superuser account as well if you wish to use django's admin app:

    python manage.py createsuperuser

# Run the app locally

Start django's local server from a terminal:

    python manage.py runserver

(hit Ctrl-C to stop the server anytime)

The app will be available at the address http://127.0.0.1:8000/litrevu/

# Manage the app as superuser

If not already done, create a superadmin account:

    python manage.py createsuperuser

then run the local server, and go to: http://127.0.0.1:8000/admin

# Clear the database

If you want to restore the database from fixtures, you must first clear the database before loading the fixtures.

The **cleardata** command was added to *django-admin* to clear the models form the database, yet without changing its schema:

    python manage.py cleardata

# Configuration, testing and debugging

**Settings for Django** are located in `litrevu/settings.py`.

The **[Django debug toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/)** is already set up, a `DISPLAY_DEBUG_TOOLBAR` flag in `settings.py` controls wether it should run.

The app's **unit tests** are found in `app/tests.py`. The tests require the test fixtures found in `app/fixtures/tests.yaml`.
