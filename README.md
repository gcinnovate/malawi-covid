CPMR
=====
The UNICEF/MoH Malawi COVID-19 Response SMS solution backend application with the RapidPro webhook endpoints.

How to Set up the development server
1. Clone the application from Github

$ git clone https:/github.com/gcinnovate/malawi-covid.git

$ cd malawi-covid

2. Create and activate virtual environment

$ python3 -m venv env

$ . env/bin/activate

3. Install Dependencies

$ pip install -r requirements.txt

4. Configuration
The configurations for the CPMR application are made using environment variables.
Refer to the config.py file for the environment variables to set.

$ export FLASK_APP=covid.py

$ export FLASK_CONFIG=default

$ export DEV_DATABASE_URL=postgresql://postgres:postgres@localhost/covid

5. Migrate database

$ flask db upgrade

6. Populate database with locations and police stations

$ flask initdb
This runs the initdb command in the covid.py application script to initialize database with some data

7. There are two commands available to help load some test data.

$ flask load_test_data

$ flask load_test_data2

You can use the --help option on each of the commands to see some arguments you can pass to the commands.

8. To creating views to use as data sources, we use the following flask command

$ flask create-views

9. Creating an admin user

$ flask create-user

10. Running the application

$ flask run

$ celery worker -A celery_worker.celery --loglevel=info
