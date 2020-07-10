from .. import (
        db, celery, INDICATORS, RAPIDPRO_API_TOKEN, RAPIDPRO_API_URL, USE_DISPATCHER2,
        DISPATCHER2_SOURCE_APP as sourceApp,
        DISPATCHER2_DHIS2_TEI_APP as trackedEntityInstanceApp,
         DHIS2_TEI_ENDPOINT, DHIS2_EVENTS_ENDPOINT)
from ..models import FlowData
from ..utils import (
        get_indicators_from_rapidpro_results, compose_tracked_entity_instance_payload,
        queue_payload_for_dhis2, post_data_to_dhis2, get_tracked_entity_instance_reference,
        compose_event_payload_list)
from datetime import datetime
import calendar
import requests
import json
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

MONTHS_DICT = dict((v, k) for k, v in enumerate(calendar.month_name))


@celery.task(name="tasks.save_flowdata")
def save_flowdata(
        request_args, request_json, districts):
    msisdn = request_args.get('msisdn')
    report_type = request_args.get('report_type')
    if not request_json:
        logger.info("EMPTY Post Data from RapidPro! [Report: {0}, MSISDN: {1}]".format(report_type, msisdn))
        return

    flowdata = get_indicators_from_rapidpro_results(
        request_json['results'], INDICATORS, report_type)
    # get district from flowdata
    district = flowdata.get('district').title()

    # normalize date
    date_of_birth = flowdata.get('dob', '').split('T')[0]
    flowdata['dob'] = date_of_birth

    month = datetime.now().month
    if report_type in ('covid', 'reg'):
        year = datetime.now().year

    month_str = "{0}-{1:02}".format(year, month)

    # redis_client.districts set using @app.before_first_request
    ids = districts.get(district)
    if ids:
        district_id = ids['id']
        region_id = ids['parent_id']
        if report_type in ('covid'):
            logger.info('Handling COVID Data for MSISDN: {0}'.format(msisdn))
            value_record = FlowData.query.filter_by(
                report_type=report_type, msisdn=msisdn).first()

            if value_record:
                value_record.values = flowdata
                value_record.msisdn = msisdn
                value_record.updated = datetime.now()

                # url_suffix is added to /trackedEntityInstance endpoint
                # used for updates
                if value_record.instanceid:
                    url_suffix = "/{}".format(value_record.instanceid)
                else:
                    url_suffix = ""

            else:
                value_record = FlowData(
                    msisdn=msisdn, district=district_id, region=region_id,
                    report_type=report_type, month=month_str, year=year, values=flowdata)
                db.session.add(value_record)

                url_suffix = ""

            try:
                db.session.commit()
            except:
                db.session.rollback()
                logger.info('DB ERROR: [COVID] [MSISDN: {0}, District: {1}, [MONTH: {2}]'.format(
                    msisdn, district, month_str))

            # Queue for DHIS 2 submission to create a TEI
            orgUnitId = ids['uid']
            payload = compose_tracked_entity_instance_payload(flowdata, orgUnitId)
            print(payload)
            if USE_DISPATCHER2:
                params = {
                    'source': sourceApp,
                    'destination': trackedEntityInstanceApp,
                    'ctype': 'json',
                    'msgid': value_record.id,
                    'body': payload,
                    'wk': '',
                    'month': month,
                    'yr': year,
                    'tel': msisdn,
                    'raw_msg': '',
                    'report_type': 'covid',
                    'status': 'ready',
                    'body_qparams': 'f',
                    'extras': '{}',
                    'facility': '',
                    'district': district,
                    'url_suffix': url_suffix
                }
                queue_payload_for_dhis2(params)
                eventPayloadList = compose_event_payload_list(flowdata, orgUnitId)
            else:
                method = "PUT" if url_suffix else "POST"
                url = DHIS2_TEI_ENDPOINT
                if url_suffix:
                    url += url_suffix
                try:
                    resp = post_data_to_dhis2(url, payload, method=method)
                    reference = get_tracked_entity_instance_reference(resp.json())
                    print("+++++++", resp.json())
                    print(">>>>>>>>", reference)
                    if method == "POST":
                        value_record.instanceid = reference
                        db.session.commit()
                    if not reference:
                        reference = url_suffix.replace("/", "")

                    # Get the list of event payloads for each stage
                    eventPayloadList = compose_event_payload_list(flowdata, orgUnitId, reference)
                    print("====>", eventPayloadList)
                    eventsEndpoint = DHIS2_EVENTS_ENDPOINT
                    # create the events
                    for p in eventPayloadList:
                        resp = post_data_to_dhis2(eventsEndpoint, json.dumps(p))
                        print(resp.json())

                except Exception as e:
                    logger.info("Trouble Submitting to DHIS 2: [URL:{0}][ERROR: {1}]".format(
                        url, str(e)))

        logger.info('Done processing flow values')
    else:
        logger.info("district ids empty for MSISDN: {0}, District: {1}".format(msisdn, district))


@celery.task(name="send_sms_notification")
def send_sms_notification(message, recipients=[]):
    """message = the message to send, recipients is a list ot telephone numbers"""
    broadcasts_endpoint = RAPIDPRO_API_URL + "broadcasts.json"
    params = {
        'urns': ["tel:{}".format(tel) for tel in recipients],
        'text': message
    }
    post_data = json.dumps(params)
    try:
        requests.post(broadcasts_endpoint, post_data, headers={
            'Content-type': 'application/json',
            'Authorization': 'Token %s' % RAPIDPRO_API_TOKEN})
        # print("Broadcast Response: ", resp.text)
    except:
        print("ERROR Sending Broadcast")


@celery.task(name="update_symptoms_task")
def update_symptoms_task(request_args, request_json, districts):
    msisdn = request_args.get('msisdn')
    report_type = request_args.get('report_type')
    district = request_args.get('district').title()
    if not request_json:
        logger.info("EMPTY Post Data from RapidPro! [Report: {0}, MSISDN: {1}]".format(report_type, msisdn))
        return

    flowdata = get_indicators_from_rapidpro_results(
        request_json['results'], INDICATORS, report_type)

    ids = districts.get(district)
    if ids:
        flowdata_obj = FlowData.query.filter_by(
            report_type=report_type, msisdn=msisdn).first()
        # print("+++=+++=+++", flowdata_obj, msisdn, district)

        if flowdata_obj and flowdata_obj.instanceid:
            # we have an object
            orgUnitId = ids['uid']
            eventPayloadList = compose_event_payload_list(
                    flowdata, orgUnitId, flowdata_obj.instanceid)
            # print("====>", eventPayloadList)
            eventsEndpoint = DHIS2_EVENTS_ENDPOINT
            # create the events
            for p in eventPayloadList:
                resp = post_data_to_dhis2(eventsEndpoint, json.dumps(p))
                # print(resp.json())
