from flask import jsonify, request
from . import api
from .. import CASE_MESSAGE_TEMPLATE, SUSPECTS_MESSAGE_TEMPLATE
from string import Template
from .tasks import send_sms_notification
from ..models import NotifyingParties, Location


@api.route('/notify', methods=['GET'])
def notify():
    # districts = redis_client.districts
    # rapid_response_team = redis_client.rapid_response_team
    # global_notifying_parties = redis_client.global_notifying_parties
    name = request.args.get('name', '')
    district = request.args.get('district', '')
    phone = request.args.get('phone', '')
    status = request.args.get('status', '')
    address = request.args.get('address', '')
    print("Name: {}, Phone:{}, Disrict:{}, Status:{}".format(name, phone, district, status))
    if status == "Suspect":
        msg_template = SUSPECTS_MESSAGE_TEMPLATE if SUSPECTS_MESSAGE_TEMPLATE else (
            "Hello, ${name} (${phone}) from ${district} district ${address} "
            "has been identified as a COVID-19 suspect")
    else:
        msg_template = CASE_MESSAGE_TEMPLATE if CASE_MESSAGE_TEMPLATE else (
            "Hello, ${name} (${phone}) from ${district} district ${address} "
            "has been confirmed as a COVID-19 case ")
    message = Template(msg_template).safe_substitute({
        'name': name, 'phone': phone, 'district': district, 'address': address})

    rapid_response_team = NotifyingParties.query.filter_by(
            reporter_type='rrt',
            district=Location.query.filter_by(name=district).first()).with_entities('msisdn').all()
    global_notifying_parties = NotifyingParties.query.filter_by(
            reporter_type='phim').with_entities('msisdn').all()

    recipients = [i[0] for i in rapid_response_team]
    recipients_2 = [i[0] for i in global_notifying_parties]

    recipients.extend(recipients_2)
    print(recipients, message)
    # send_sms_notification.delay(message, recipients)
    return jsonify({'message': 'success'})
