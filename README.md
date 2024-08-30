# oc-lit-revu

Openclassrooms Python Project 9

A community book reviewing app

## Dependencies and requirements

This app requires [Python 3.8+](https://www.python.org/) and [Django 5.1](https://www.djangoproject.com/) (see installation notes below).

The app's database is powered by SQLite3 (shipped with Python by default).

## Installation

clone this repository:

    git clone git@github.com:christian-debray/oc-litrevu.git .

install a python virtual envirionment:

    python -m venv env

run the virtual environment:

    source env/bin/activate

install the required packages

    pip install -r requirements.txt

## Run the app locally

Start django's local server from a terminal:

    python manage.py runserver

(hit Ctrl-C to stop the server anytime)

The app will be available at adress http://127.0.0.1:8000/litrevu/

## Manage the app as superuser

create a superadmin account:

    python manage.py createsuperuser

then run the local server, and go to :

http://127.0.0.1:8000/litrevu/admin
