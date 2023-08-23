from app import app, mongo
from flask import jsonify
from datetime import datetime
from calendar import monthrange

@app.route('/')
def home():
    return 'Dashboard backend working'

@app.route('/summary/<month_year>', methods=['GET'])
def summary(month_year):
    try:
        # Validate MM-YYYY format
        if not (len(month_year) == 7 and month_year[2] == '-'):
            return jsonify({"error": "Invalid month-year format. It should be MM-YYYY."}), 400

        # Convert "MM-YYYY" to a datetime object
        start_date = datetime.strptime(month_year, '%m-%Y')
    except ValueError:
        return jsonify({"error": "Invalid month-year format. It should be MM-YYYY."}), 400

    # Calculate the end date
    if start_date.month == 12:
        end_date = datetime(start_date.year + 1, 1, 1)
    else:
        end_date = datetime(start_date.year, start_date.month + 1, 1)

    # Calculate the start date of the previous month
    if start_date.month == 1:
        prev_month_start = datetime(start_date.year - 1, 12, 1)
    else:
        prev_month_start = datetime(start_date.year, start_date.month - 1, 1)

    prev_month_end = start_date

    # Get data from the database
    active_members_current = mongo.db.clientes.count_documents({
        "status": "activo",
        "last_subscription_date": {"$gte": start_date, "$lt": end_date}
    })

    active_members_prev = mongo.db.clientes.count_documents({
        "status": "activo",
        "last_subscription_date": {"$gte": prev_month_start, "$lt": prev_month_end}
    })

    new_members_current = mongo.db.clientes.count_documents({
        "history": {"$elemMatch": {"event": "alta", "date_created": {"$gte": start_date, "$lt": end_date}}}
    })

    new_members_prev = mongo.db.clientes.count_documents({
        "history": {"$elemMatch": {"event": "alta", "date_created": {"$gte": prev_month_start, "$lt": prev_month_end}}}
    })

    unsub_members_current = mongo.db.clientes.count_documents({
        "history": {"$elemMatch": {"event": "baja", "date_created": {"$gte": start_date, "$lt": end_date}}}
    })

    unsub_members_prev = mongo.db.clientes.count_documents({
        "history": {"$elemMatch": {"event": "baja", "date_created": {"$gte": prev_month_start, "$lt": prev_month_end}}}
    })

    # For inactive members, we consider those who lost their validity without requesting a cancellation.
    inactive_members_current = mongo.db.clientes.count_documents({
        "status": "inactivo",
        "fecha_vigencia": {"$gte": start_date, "$lt": end_date},
        "history": {"$not": {"$elemMatch": {"event": "baja", "date_created": {"$gte": start_date, "$lt": end_date}}}}
    })

    inactive_members_prev = mongo.db.clientes.count_documents({
        "status": "inactivo",
        "fecha_vigencia": {"$gte": prev_month_start, "$lt": prev_month_end},
        "history": {"$not": {"$elemMatch": {"event": "baja", "date_created": {"$gte": prev_month_start, "$lt": prev_month_end}}}}
    })

    # Calculate percentage variations
    def calc_variation(current, prev):
        return ((current - prev) / prev) * 100 if prev != 0 else 100

    return jsonify({
        'active_members': active_members_current,
        'active_members_variation': calc_variation(active_members_current, active_members_prev),
        'new_members': new_members_current,
        'new_members_variation': calc_variation(new_members_current, new_members_prev),
        'unsub_members': unsub_members_current,
        'unsub_members_variation': calc_variation(unsub_members_current, unsub_members_prev),
        'inactive_members': inactive_members_current,
        'inactive_members_variation': calc_variation(inactive_members_current, inactive_members_prev)
    }), 200

@app.route('/charges/<month_year>', methods=['GET'])
def charges(month_year):
    try:
        if not (len(month_year) == 7 and month_year[2] == '-'):
            return jsonify({"error": "Invalid month-year format. It should be MM-YYYY."}), 400
        
        start_date = datetime.strptime(month_year, '%m-%Y')
    except ValueError:
        return jsonify({"error": "Invalid month-year format. It should be MM-YYYY."}), 400
    
    if start_date.month == 12:
        end_date = datetime(start_date.year + 1, 1, 1)
    else:
        end_date = datetime(start_date.year, start_date.month + 1, 1)
    
    try:
        pipeline = [
            {
                "$match": {
                    "date_created": {"$gte": start_date, "$lt": end_date},
                    "status": "approved",
                    "source": {"$in": ["recurring_charges", "Recurring_miclub", "checkout", "checkout3", "checkout_miclub"]}
                }
            },
            {
                "$group": {
                    "_id": {
                        "day": {"$dayOfMonth": "$date_created"},
                        "type": {
                            "$cond": {
                                "if": {"$in": ["$source", ["checkout", "checkout3", "checkout_miclub"]]},
                                "then": "alta",
                                "else": "recurrente"
                            }
                        }
                    },
                    "total": {"$sum": "$charges_detail.final_price"}
                }
            },
            {
                "$group": {
                    "_id": "$_id.type",
                    "data": {
                        "$push": {
                            "day": "$_id.day",
                            "total": "$total"
                        }
                    }
                }
            },
            {
                "$project": {
                    "type": "$_id",
                    "_id": 0,
                    "data": 1
                }
            }
        ]

        result = list(mongo.db.boletas.aggregate(pipeline))

        # Creation of dictionaries
        days_in_month = monthrange(start_date.year, start_date.month)[1]
        up_data = {day: 0 for day in range(1, days_in_month + 1)}
        recurring_data = {day: 0 for day in range(1, days_in_month + 1)}

        for item in result:
            type_ = item['type']

            for entry in item['data']:
                if type_ == "alta":
                    up_data[entry['day']] = entry['total']
                else:
                    recurring_data[entry['day']] = entry['total']

        return jsonify({
            "up": up_data,
            "recurring": recurring_data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/total-values/<business>/<month_year>', methods=['GET'])
def total_values(business, month_year):
    try:
        if not (len(month_year) == 7 and month_year[2] == '-'):
            return jsonify({"error": "Invalid month-year format. It should be MM-YYYY."}), 400
        
        start_date = datetime.strptime(month_year, '%m-%Y')
    except ValueError:
        return jsonify({"error": "Invalid month-year format. It should be MM-YYYY."}), 400
    
    if start_date.month == 12:
        end_date = datetime(start_date.year + 1, 1, 1)
    else:
        end_date = datetime(start_date.year, start_date.month + 1, 1)
    
    if start_date.month == 1:
        prev_month_start = datetime(start_date.year - 1, 12, 1)
    else:
        prev_month_start = datetime(start_date.year, start_date.month - 1, 1)

    prev_month_end = start_date

    # Get merchant_id
    merchant = mongo.db.merchants.find_one({"name": business})

    if not merchant:
        return jsonify({"error": "Merchant not found."}), 404
    
    merchant_id = merchant['_id']
    
    def total_pipeline(start, end):
        total_pipeline = [
            {
                "$match": {
                    "merchant_id": merchant_id,
                    "status": "approved",
                    "date_created": {
                        "$gte": start,
                        "$lte": end
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_charged": {"$sum": "$charges_detail.final_price"}
                }
            }
        ]

        return list(mongo.db.boletas.aggregate(total_pipeline))

    total_results = total_pipeline(start_date, end_date)
    total_results = total_results[0]['total_charged'] if total_results else 0
    total_results_variation = total_pipeline(prev_month_start, prev_month_end)
    total_results_variation = total_results_variation[0]['total_charged'] if total_results else 0

    def get_amounts(start_date, end_date):
        pipeline = [
            {
                "$match": {
                    "merchant_id": merchant_id, 
                    "status": "approved", 
                    "date_created": {"$gte": start_date, "$lte": end_date}
                }
            },
            {"$group": {"_id": "$source", "total": {"$sum": "$charges_detail.final_price"}}}
        ]
        
        return {entry['_id']: entry['total'] for entry in mongo.db.boletas.aggregate(pipeline)}
    
    current_month_amounts = get_amounts(start_date, end_date)
    previous_month_amounts = get_amounts(prev_month_start, prev_month_end)

    def calculate_variation(current, prev):
        return ((current - prev) / prev) * 100 if prev != 0 else 100

    result = {
        "total_charged": total_results,
        "total_charged_variation": calculate_variation(total_results, total_results_variation),
        "recurrencias": current_month_amounts.get('recurring_charges', 0),
        "variacion_recurrencias": calculate_variation(current_month_amounts.get('recurring_charges', 0), previous_month_amounts.get('recurring_charges', 0)),
        "altas": sum([current_month_amounts.get(source, 0) for source in ['checkout', 'checkout3', 'checkout_miclub']]),
        "variacion_altas": calculate_variation(sum([current_month_amounts.get(source, 0) for source in ['checkout', 'checkout3', 'checkout_miclub']]), sum([previous_month_amounts.get(source, 0) for source in ['checkout', 'checkout3', 'checkout_miclub']])),
    }
    
    return jsonify(result)

@app.route('/pie-chart/<month_year>', methods=['GET'])
def pie_chart(month_year):
    try:
        if not (len(month_year) == 7 and month_year[2] == '-'):
            return jsonify({"error": "Invalid month-year format. It should be MM-YYYY."}), 400

        start_date = datetime.strptime(month_year, '%m-%Y')
    except ValueError:
        return jsonify({"error": "Invalid month-year format. It should be MM-YYYY."}), 400
    
    if start_date.month == 12:
        end_date = datetime(start_date.year + 1, 1, 1)
    else:
        end_date = datetime(start_date.year, start_date.month + 1, 1)

    try:
        total_result = mongo.db.boletas.aggregate([
            {"$match": {"date_created": {"$gte": start_date, "$lt": end_date}, "status": "approved"}},
            {"$group": {"_id": None, "total": {"$sum": "$charges_detail.final_price"}}}
        ])

        for res in total_result:
            total_charged = res["total"]
        
        charge_pipeline = [
            {"$match": {"date_created": {"$gte": start_date, "$lt": end_date}, "status": "approved"}},
            {"$lookup": {
                "from": "planes",
                "localField": "plan_id",
                "foreignField": "_id",
                "as": "plan_info"
            }},
            {"$unwind": "$plan_info"},
            {"$group": {
                "_id": "$plan_info.cobro",
                "monto": {"$sum": "$charges_detail.final_price"}
            }}
        ]

        access_pipeline = [
            {"$match": {"date_created": {"$gte": start_date, "$lt": end_date}, "status": "approved"}},
            {"$lookup": {
                "from": "planes",
                "localField": "plan_id",
                "foreignField": "_id",
                "as": "plan_info"
            }},
            {"$unwind": "$plan_info"},
            {"$group": {
                "_id": "$plan_info.nivel_de_acceso",
                "monto": {"$sum": "$charges_detail.final_price"}
            }}
        ]

        result_charge = mongo.db.boletas.aggregate(charge_pipeline)
        result_access = mongo.db.boletas.aggregate(access_pipeline)

        # Format results
        formatted_charge = {}
        formatted_access = {}

        for res in result_charge:
            cobro_type = res["_id"]
            percentage = (res["monto"] / total_charged) * 100
            formatted_charge[cobro_type] = round(percentage, 2)

        for cobro_type in ["Mensual", "Anual"]:
            if cobro_type not in formatted_charge:
                formatted_charge[cobro_type] = 0
        
        for res in result_access:
            access_type = res["_id"]
            percentage = (res["monto"] / total_charged) * 100
            formatted_access[access_type] = round(percentage, 2)
        
        for access_type in ["Local", "Total", "Plus"]:
            if access_type not in formatted_access:
                formatted_access[access_type] = 0
        
        return jsonify({
            "charges": formatted_charge,
            "access": formatted_access
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
