from flask import jsonify, request
from . import api
from .. import redis_client, GLOBAL_STATS_ENDPOINT
from ..models import FlowData
import requests


@api.route('/stats', methods=['GET'])
def stats():
    # global_stats = redis_client.global_stats
    isGlobal = request.args.get('global', 'true')
    # nationality = request.args.get('global', 'Malawi')

    try:
        stats_record = FlowData.query.filter_by(report_type='stats').first()
        print(type(stats_record.values))
        stats = stats_record.values
        if stats:
            if isGlobal == 'true':
                return jsonify(stats['global'])
            else:
                return jsonify(stats['local'])
        # resp = requests.get(GLOBAL_STATS_ENDPOINT)
        # stats = resp.json()
        # gstats = stats.get('Global')

        # msg = msg.format(**gstats)
        # print(msg)
        # redis_client.global_stats = gstats
        # # return jsonify({'message': msg})
        # return jsonify(gstats)
    except Exception as e:
        # gstats = redis_client.global_stats
        # if gstats:
        #     print(">>>", gstats)
        #     msg.format(**gstats)
        #     # return jsonify({'message': msg})
        #     return jsonify(gstats)
        print("Failed to get stats ", str(e))

    return jsonify(redis_client.global_stats)
