from .. import db, celery, INDICATORS, RAPIDPRO_API_TOKEN, RAPIDPRO_API_URL
from ..models import FlowData
from ..utils import get_indicators_from_rapidpro_results
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
    district = request_args.get('district').title()
    if not request_json:
        logger.info("EMPTY Post Data from RapidPro! [Report: {0}, MSISDN: {1}]".format(report_type, msisdn))
        return

    flowdata = get_indicators_from_rapidpro_results(
        request_json['results'], INDICATORS, report_type)
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
                year=year, month=month_str, report_type=report_type, msisdn=msisdn).first()

            if value_record:
                value_record.values = flowdata
                value_record.msisdn = msisdn
                value_record.updated = datetime.now()
            else:
                db.session.add(FlowData(
                    msisdn=msisdn, district=district_id, region=region_id,
                    report_type=report_type, month=month_str, year=year, values=flowdata))
            try:
                db.session.commit()
            except:
                db.session.rollback()
                logger.info('DB ERROR: [COVID] [MSISDN: {0}, District: {1}, [MONTH: {2}]'.format(
                    msisdn, district, month_str))

        logger.info('Done processing flow values')
    else:
        logger.info("district ids empty for MSISDN: {0}, District: {1}".format(msisdn, district))


@celery.task(name="")
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
