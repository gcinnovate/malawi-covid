from flask import jsonify, request
from .. import db
from ..models import FlowData, Location
from . import api
# from .decorators import permission_required
# from .errors import forbidden
from .. import redis_client
from .tasks import save_flowdata, update_symptoms_task

@api.route('/flowdata')
def get_flowdata():
    return "Text flow data"


@api.route('/flowdata/', methods=['POST'])
def flowdata_webhook():

    # redis_client.districts set using @app.before_first_request
    # districts = redis_client.districts
    locs = Location.query.filter_by(level=3).all()
    districts = {}
    for l in locs:
        districts[l.name] = {'id': l.id, 'parent_id': l.parent_id, 'uid': l.dhis2id}

    report_type = request.args.get('report_type', 'covid')

    if report_type in ('covid'):
        save_flowdata.delay(
            request.args, request.json, districts)

    return jsonify({'message': 'success'})


@api.route('/teiCallback', methods=['POST'])
def tracked_entity_instance_callback():
    msg_id = request.args.get('msgid', '')  # the id in FlowData
    try:
        response = request.json.get('response')
        if response:
            if response.get("importSummaries"):
                if len(response["importSummaries"]):
                    importSummary = response["importSummaries"][0]
                    reference = importSummary["reference"]
                    flowdata_obj = FlowData.query.filter_by(id=msg_id).first()
                    if flowdata_obj:
                        flowdata_obj.instanceid = reference
                        db.session.commit()
                    return jsonify({'message': reference})
    except Exception as e:
        print(str(e))
    return jsonify({'message': 'success'})


@api.route('/updateSymptoms', methods=['POST'])
def update_symptoms():

    locs = Location.query.filter_by(level=3).all()
    districts = {}
    for l in locs:
        districts[l.name] = {'id': l.id, 'parent_id': l.parent_id, 'uid': l.dhis2id}
    update_symptoms_task.delay(request.args, request.json, districts)

    return jsonify({'message': 'success'})


