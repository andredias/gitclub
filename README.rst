GitClub
=======

https://github.com/osohq/gitclub


GitClub (Python - SQLAlchemy - Flask - React)
=============================================

This is an example application based on GitHub that's meant to model GitHub's permissions system. The app uses the oso library to model, manage, and enforce authorization.

The Oso documentation is a good reference for more information on Oso's Python integration.


Backend
=======


Running tests
-------------

$ cd backends/flask-sqlalchemy
$ python3 -m venv venv && source venv/bin/activate
$ pip3 install -r requirements.txt -r requirements-dev.txt
$ make -C ../../tests test-flask-sqlalchemy


Running the Backend
-------------------

First set up a virtualenv and install dependencies:

$ cd backends/flask-sqlalchemy
$ python3 -m venv venv && source venv/bin/activate
$ pip3 install -r requirements.txt

If this is the first time you've run the app, pass True as the second argument to create_app(), which seeds the database from the app/fixtures.py file:

$ FLASK_APP="app:create_app(None, True)" flask run

If you've already seeded the database, change True to False to avoid resetting the database:

$ FLASK_APP="app:create_app(None, False)" flask run


Architecture
------------

* Python / SQLAlchemy / Flask
* SQLite for persistence


Data Model
----------

The app has the following models:

* ``Org`` - the top-level grouping of users and resources in the app. As with GitHub, users can be in multiple orgs and may have different permission levels in each.
* ``User`` - identified by email address, users can have roles within orgs and repos.
* ``Repo`` - mimicking repos on GitHub — but without the backing Git data — each belongs to a single org.
* ``Issue`` - mimicking GitHub issues, each is associated with a single repo.
* ``OrgRole`` - a user role on an organization.
* ``RepoRole`` - a user role on a repository.


Authorization Model
-------------------

Users can have roles on orgs and/or repos. Roles are defined in app/authorization.polar.


Frontend
========


Running the frontend
--------------------

$ cd frontend
$ yarn
$ yarn start


Architecture
------------

* TypeScript / React / Reach Router
