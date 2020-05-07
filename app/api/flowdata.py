from flask import jsonify, request
# from .. import db, INDICATORS
# from ..models import FlowData, Permission
from . import api
# from .decorators import permission_required
# from .errors import forbidden
from .. import redis_client
from .tasks import save_flowdata


@api.route('/flowdata')
def get_flowdata():
    return "Text flow data"


@api.route('/flowdata/', methods=['POST'])
def flowdata_webhook():

    # redis_client.districts set using @app.before_first_request
    districts = redis_client.districts
    report_type = request.args.get('report_type', '')

    if report_type in ('covid'):
        save_flowdata.delay(
            request.args, request.json, districts)

    return jsonify({'message': 'success'})
