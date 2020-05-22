import os
# import sys
import string
import random
from openpyxl import load_workbook
import click
from dotenv import load_dotenv
from flask_migrate import Migrate, upgrade
from app import create_app, db, redis_client
from app.models import (
    Location, LocationTree, User, Role,
    FlowData, SummaryCases, NotifyingParties)
import datetime
import requests
from flask import current_app
from sqlalchemy.sql import text
from getpass import getpass

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.before_first_request
def before_first_request_func():
    locs = Location.query.filter_by(level=3).all()
    districts = {}
    rapid_response_team = {}  # Each district name will be a key with a list of numbers a value
    for l in locs:
        districts[l.name] = {'id': l.id, 'parent_id': l.parent_id}
        rapid_response_team[l.name] = []

    redis_client.districts = districts
    global_notifying_parties = []  # A list of contacts of teams that receive all notifications e.g PHIM

    notifying_parties = NotifyingParties.query.all()
    for p in notifying_parties:
        if p.reporter_type == 'rrt' and p.district:
            rapid_response_team[p.district.name].append(p.msisdn)
        if p.reporter_type == 'phim':
            global_notifying_parties.append(p.msisdn)
    redis_client.rapid_response_team = rapid_response_team
    redis_client.global_notifying_parties = global_notifying_parties
    statsUrl = os.environ.get('GLOBAL_STATS_ENDPOINT', 'https://api.covid19api.com/summary')
    try:
        resp = requests.get(statsUrl)
        redis_client.global_stats = resp.json()['Global']
    except:
        redis_client.global_stats = {}
    # print(global_notifying_parties)
    # print(rapid_response_team)
    # print("This function will run once")


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


@app.teardown_appcontext
def teardown_db(exception=None):
    db.session.remove()


@app.cli.command("initdb")
def initdb():
    def id_generator(size=12, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    Role.insert_roles()
    country = Location.query.filter_by(name='Malawi', level=1).all()
    if country:
        click.echo("Database Already Initialized")
        return

    click.echo("Database Initialization Starting.............!")

    db.session.add(LocationTree(name='Malawi Administrative Divisions'))
    db.session.commit()
    # Add country
    db.session.add(Location(name='Malawi', code=id_generator(), tree_id=1))  # Country
    # Add the regions
    db.session.add_all(
        [
            Location(name='Central', code=id_generator(), parent_id=1, tree_id=1),  # 2
            Location(name='Eastern', code=id_generator(), parent_id=1, tree_id=1),  # 3
            Location(name='Northern', code=id_generator(), parent_id=1, tree_id=1),  # 4
            Location(name='Southern', code=id_generator(), parent_id=1, tree_id=1),  # 5
        ]
    )

    # Central = 2, Eastern = 3, Northern = 4, Southern = 5
    regions_data = {
        '2': [
            'Dedza', 'Dowa', 'Kasungu', 'Lilongwe', 'Mchinji',
            'Nkhotakota', 'Ntcheu', 'Ntchisi', 'Salima'],
        '3': ['Balaka', 'Machinga', 'Mangochi', 'Zomba'],
        '4': ['Chitipa', 'Karonga', 'Likoma', 'Mzimba', 'Nkhata Bay', 'Rumphi'],
        '5': [
            'Blantyre', 'Chikwawa', 'Chiradzulu', 'Mulanje', 'Mwanza', 'Neno', 'Nsanje',
            'Phalombe', 'Thyolo']
    }
    for k, v in regions_data.items():
        for val in v:
            db.session.add(Location(name=val, code=id_generator(), parent_id=k, tree_id=1))
    db.session.commit()

    click.echo("Database Initialization Complete!")


@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # migrate database to latest revision
    upgrade()


@app.cli.command("create-user")
def createuser():
    username = input("Enter Username: ")
    email = input("Enter Email: ")
    password = getpass()
    cpass = getpass("Confirm Password: ")
    assert password == cpass
    u = User(username=username, email=email)
    u.password = cpass
    db.session.add(u)
    db.session.commit()
    u.confirmed = True
    db.session.commit()
    click.echo("User added!")


@app.cli.command("create-views")
def create_views():
    with current_app.open_resource('../views.sql') as f:
        # print(f.read())
        click.echo("Gonna create views")
        db.session.execute(text(f.read().decode('utf8')))
        db.session.commit()
        click.echo("Done creating views")


@app.cli.command("refresh-pie-charts")
def refresh_pie_charts():
    pass
