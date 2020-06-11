from . import (
    AUTO_MONTH_FLOWS,
    DISPATCHER2_DATABASE_URI,
    DHIS2_TRACKER_PROGRAM_CONF as programConf,
    DHIS2_USERNAME, DHIS2_PASSWORD)
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import datetime
import json
import base64
import requests

db = create_engine(DISPATCHER2_DATABASE_URI)


def post_data_to_dhis2(url, data, params={}, method="POST"):
    user_pass = '{0}:{1}'.format(DHIS2_USERNAME, DHIS2_PASSWORD)
    coded = base64.b64encode(user_pass.encode())
    if method == "PUT":
        payload = json.loads(data).pop('enrollments')
        response = requests.put(
            url, data=json.dumps(payload), headers={
                'Content-Type': 'application/json',
                'Authorization': 'Basic ' + coded.decode()},
            verify=False, params=params
        )
    else:
        response = requests.post(
            url, data=data, headers={
                'Content-Type': 'application/json',
                'Authorization': 'Basic ' + coded.decode()},
            verify=False, params=params
        )
    return response


def get_indicators_from_rapidpro_results(results_json, indicator_conf={}, report_type=None):
    report_type_indicators = indicator_conf.get(report_type, [])
    # we shall have to sum up the aggregate inidicators to get a total
    flow_inidicators = {}

    for k, v in results_json.items():
        if k in report_type_indicators:
            if k == 'month':
                if report_type in AUTO_MONTH_FLOWS:
                    flow_inidicators[k] = results_json[k]['value']
                else:
                    flow_inidicators[k] = results_json[k]['category']
            else:
                try:
                    flow_inidicators[k] = int(results_json[k]['value'])
                except:
                    flow_inidicators[k] = results_json[k]['value']
            # sum up aggregate indicators

    return flow_inidicators


def compose_tracked_entity_instance_payload(values, orgUnitId):
    payload = {
        'trackedEntityType': programConf['trackedEntityType'],
        'orgUnit': orgUnitId,
        'attributes': [],
        'enrollments': [{
            'orgUnit': orgUnitId,
            'program': programConf['program'],
            'enrollmentDate': datetime.datetime.now().strftime('%Y-%m-%d'),
            'incidentDate': datetime.datetime.now().strftime('%Y-%m-%d')
        }]

    }

    values['firstname'] = ' '.join(values.get('name', '').split()[:1])
    values['lastname'] = ' '.join(values.get('name', '').split()[1:])

    for k, v in values.items():
        if k in programConf.get('attributes'):
            payload['attributes'].append({
                'attribute': programConf['attributes'][k],
                'value': v
            })
    return json.dumps(payload)


def compose_event_payload_list(values, orgUnitId, trackedEntityInstance):
    """Returns a list of payloads for different stages in the program"""
    payload = {
        'program': programConf['program'],
        'orgUnit': orgUnitId,
        'trackedEntityInstance': trackedEntityInstance,
        'eventDate': datetime.datetime.now().strftime('%Y-%m-%d'),
        'status': 'COMPLETED',
        'completedDate': datetime.datetime.now().strftime('%Y-%m-%d'),
        'storedBy': DHIS2_USERNAME,
        'dataValues': []
    }
    programEventsPayloadList = []
    for stage, stageConf in programConf['stages'].items():
        stub = payload.copy()
        stub['programStage'] = stageConf['uid']
        for k, v in stageConf['dataelements'].items():
            if k in values:
                stub['dataValues'].append({'dataElement': v, 'value': values[k]})
        programEventsPayloadList.append(stub)

    return programEventsPayloadList

def queue_payload_for_dhis2(params, engine=db):

    statement = text("""
        INSERT INTO requests(source, destination, body, ctype, submissionid, week,
            month, year, msisdn, raw_msg, facility, district, report_type, status,
            body_is_query_param, extras, url_suffix)
            VALUES((SELECT id FROM servers WHERE name = :source),
                (SELECT id FROM servers WHERE name = :destination), :body, :ctype, :msgid, :wk, :month, :yr, :tel,
                :raw_msg, :facility, :district, :report_type, :status, :body_qparams, :extras, :url_suffix)
            """)
    with engine.connect() as con:
        con.execute(statement, **params)


def get_tracked_entity_instance_reference(responseObj):
    """returns the reference i.e UID of trackedEntityInstance from DHIS2 response"""
    try:
        response = responseObj.get('response')
        if response:
            if response.get("importSummaries"):
                if len(response["importSummaries"]):
                    importSummary = response["importSummaries"][0]
                    reference = importSummary["reference"]
                    return reference
    except Exception as e:
        print(str(e))
    return ''
