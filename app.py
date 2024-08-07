import pandas as pd
import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from calculator import (calculate_months, calculate_value,
                        eligibility, format_currency)
from utils import (save_to_csv, save_transposed_to_csv)

# to do
# refactor code so that it has been simplified
# try to make the fields which are shared across as json more standardised
# rename variables to mirror swift
# mirror changes in v2 of app
# add guardrails in app

# static variables
db = 'consumer_retention'
db_schema_searches = f'{db}-searches.csv'
db_schema_form = f'{db}-registration-details.csv'
db_schema_outcomes = f'{db}-outcomes.csv'

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/direct')
def direct():
    return render_template('direct.html')

@app.route('/intermediary')
def intermediary():
    return render_template('intermediary.html')

@app.route('/training')
def training():
    return render_template('training.html')

@app.route('/calculate_offer', methods=['POST'])
def calculate_offer():
    try:
        data = request.json
        if 'intermediary' in data['url']:

            user_info = {
                'guid': str(data['guid']),
                'registration-number': float(data['registration-number']),
                'user-renewal-date': datetime.strptime(data['user-renewal-date'], '%Y-%m-%d'),
                'user-payment-frequency': data['user-payment-frequency'],
                'user-annual-subs': float(data['user-annual-subs']),
                'user-months-arrears': float(data['user-months-arrears']),
                'user-financial-distress': 0,
                'user-months-free-last': str(data['user-months-free-last']),
                'user-months-free-this': float(data['user-months-free-this']),
                'user-color-segment': str(data['user-color-segment']),
                'user-claims-paid': str(data['user-claims-paid']),
                'user-intermediary': str(data['user-intermediary']),
                'user-intermediary-advisor': str(data['user-intermediary-advisor']),
                'url': data.get('url')
            }

        else:

            user_info = {
                'guid': str(data['guid']),
                'registration-number': float(data['registration-number']),
                'user-renewal-date': datetime.strptime(data['user-renewal-date'], '%Y-%m-%d'),
                'user-payment-frequency': data['user-payment-frequency'],
                'user-annual-subs': float(data['user-annual-subs']),
                'user-months-arrears': float(data['user-months-arrears']),
                'user-financial-distress': 0,
                'user-months-free-last': str(data['user-months-free-last']),
                'user-months-free-this': float(data['user-months-free-this']),
                'user-color-segment': str(data['user-color-segment']),
                'user-claims-paid': str(data['user-claims-paid']),
                'url': data.get('url')
            }
        months_free = calculate_months(
            user_info['user-annual-subs'],
            user_info['registration-number'],
            user_info['user-months-arrears'],
            user_info['user-financial-distress'],
            user_info['user-months-free-last'],
            user_info['user-months-free-this'],
            user_info['user-color-segment'],
            user_info['user-claims-paid'])
        offer_bin, offer_str = eligibility(months_free)
        total_payable, value, formatted_total_payable, formatted_value = calculate_financials(user_info, months_free)

        search_csv_file_path = os.path.join('data', db_schema_searches)
        search_row_data = [user_info['guid'],
                    user_info['registration-number'],
                    user_info['url'],
                    pd.to_datetime(datetime.now())]
        save_to_csv(search_csv_file_path, search_row_data)

        form_csv_file_path = os.path.join('data', db_schema_form)

        guid = user_info['guid']
        source = 'user-input'

        # Define the fields
        fields = [
            'registration-number',
            'user-renewal-date',
            'user-payment-frequency',
            'user-annual-subs',
            'user-months-arrears',
            'user-financial-distress',
            'user-months-free-last',
            'user-months-free-this',
            'user-color-segment',
            'user-claims-paid',
            'timestamp',
            'user-intermediary',
            'user-intermediary-advisor'
        ]

        if 'intermediary' in user_info['url']:

            # Define the row data
            row_data = [
                # user_info['guid'],
                user_info['registration-number'],
                user_info['user-renewal-date'],
                user_info['user-payment-frequency'],
                user_info['user-annual-subs'],
                user_info['user-months-arrears'],
                user_info['user-financial-distress'],
                user_info['user-months-free-last'],
                user_info['user-months-free-this'],
                user_info['user-color-segment'],
                user_info['user-claims-paid'],
                datetime.now(),
                user_info['user-intermediary'],
                user_info['user-intermediary-advisor']
            ]
        else:
            # Define the row data
            row_data = [
                # user_info['guid'],
                user_info['registration-number'],
                user_info['user-renewal-date'],
                user_info['user-payment-frequency'],
                user_info['user-annual-subs'],
                user_info['user-months-arrears'],
                user_info['user-financial-distress'],
                user_info['user-months-free-last'],
                user_info['user-months-free-this'],
                user_info['user-color-segment'],
                user_info['user-claims-paid'],
                datetime.now(),
                '',
                ''
            ]

        # Prepare transposed data
        transposed_data = []
        for field, value in zip(fields, row_data):
            transposed_data.append([guid, source, field, value])

        # Function to save transposed data to CSV
        save_transposed_to_csv(form_csv_file_path, transposed_data)

        return jsonify({
            'result': offer_str,
            'eligible': offer_bin,
            'value': formatted_value,
            'total_payable': formatted_total_payable,
            'user_data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def calculate_financials(user_info, months_free):
    total_payable = calculate_value(
        user_info['user-annual-subs'],
        user_info['user-payment-frequency'],
        user_info['user-renewal-date'],
        months_free
    )
    value = user_info['user-annual-subs'] - total_payable
    formatted_total_payable = format_currency(total_payable)
    formatted_value = format_currency(value)
    return total_payable, value, formatted_total_payable, formatted_value

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        user_data = request.json.get('user_data', {})
        total_payable = request.json.get('total_payable')
        outcomes_data = request.json.get('outcomes_data', {})
        url = request.json.get('url')
        guid = request.json.get('guid')

        csv_file_path = os.path.join('data', db_schema_outcomes)

        base_row_data = [
            guid,
            datetime.now(),
            url,
            user_data.get('registration-number', ''),
            user_data.get('user-renewal-date', ''),
            user_data.get('user-annual-subs', ''),
            total_payable,
            outcomes_data.get('offer', ''),
            outcomes_data.get('offer-accepted', '')
        ]

        save_to_csv(csv_file_path, base_row_data)

        return jsonify({'message': 'Successfully submitted.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)