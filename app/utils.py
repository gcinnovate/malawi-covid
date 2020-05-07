from . import redis_client, AUTO_MONTH_FLOWS


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
