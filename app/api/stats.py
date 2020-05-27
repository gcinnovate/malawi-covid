from flask import jsonify, request
from . import api
from .. import redis_client, GLOBAL_STATS_ENDPOINT
import requests


@api.route('/stats', methods=['GET'])
def stats():
    # global_stats = redis_client.global_stats
    isGlobal = request.args.get('global', 'true')
    nationality = request.args.get('global', 'Malawi')

    msg = (
        "New Confirmed: {NewConfirmed}\nTotal Confirmed: {TotalConfirmed}\n New Deaths: "
        "{NewDeaths}\nTotal Deaths: {TotalDeaths}\nNew Recovered: {NewRecovered}"
        "\nTotal Recovered: {TotalRecovered}")

    try:
        resp = requests.get(GLOBAL_STATS_ENDPOINT)
        stats = resp.json()
        gstats = stats.get('Global')

        msg = msg.format(**gstats)
        print(msg)
        redis_client.global_stats = gstats
        # return jsonify({'message': msg})
        return jsonify(gstats)
    except:
        gstats = redis_client.global_stats
        if gstats:
            print(">>>", gstats)
            msg.format(**gstats)
            # return jsonify({'message': msg})
            return jsonify(gstats)

    return jsonify(redis_client.global_stats)
