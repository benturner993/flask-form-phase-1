from flask import Flask, render_template, request, jsonify
# from flask_azure_oauth import FlaskAzureOAuth
import os
from datetime import datetime
from calculator import (calculate_months, calculate_value,
                        eligibility, format_currency)
from utils import save_to_csv

# to do:
# add required inputs and tests on inputs
# method to save intermediary rows if they exist
# add colour icons?
# do we want to save to different schemas?

# static variables
schema = 'consumer_retention'
db_schema_1 = f'{schema}-searches.csv'
db_schema_2 = f'{schema}-outcomes.csv'

app = Flask(__name__)


# params for azure deployment
# app.config['AZURE_OAUTH_CLIENT_ID'] = '<your-client-id>'
# app.config['AZURE_OAUTH_CLIENT_SECRET'] = '<your-client-secret>'
# app.config['AZURE_OAUTH_TENANT'] = '<your-tenant-id>'

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
        user_info = extract_user_info(data)
        months_free = calculate_months_free(user_info)
        offer_bin, offer_str = eligibility(months_free)
        total_payable, value, formatted_total_payable, formatted_value = calculate_financials(user_info, months_free)
        csv_file_path = os.path.join('data', db_schema_1)
        save_outcomes(data, csv_file_path, user_info, months_free, offer_bin, offer_str, value, total_payable)

        return jsonify({
            'result': offer_str,
            'eligible': offer_bin,
            'value': formatted_value,
            'total_payable': formatted_total_payable,
            'user_data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def extract_user_info(data):
    return {
        'registration': float(data['registration-number']),
        'renewal': datetime.strptime(data['renewal-date'], '%Y-%m-%d'),
        'payment_frequency': data['payment-frequency'],
        'total_annual_subs': float(data['annual-subs']),
        'arrears': float(data['months-arrears']),
        'financial_distress': 0,
        'mf_last_year': str(data['months-free-last']),
        'mf_this_year': float(data['months-free-this']),
        'segment': str(data['color-segment']),
        'claims_paid': str(data['claims-paid']),
        'url': data.get('url')
    }

def calculate_months_free(user_info):
    return calculate_months(
        user_info['total_annual_subs'],
        user_info['registration'],
        user_info['arrears'],
        user_info['financial_distress'],
        user_info['mf_last_year'],
        user_info['mf_this_year'],
        user_info['segment'],
        user_info['claims_paid']
    )

def calculate_financials(user_info, months_free):
    total_payable = calculate_value(
        user_info['total_annual_subs'],
        user_info['payment_frequency'],
        user_info['renewal'],
        months_free
    )
    value = user_info['total_annual_subs'] - total_payable
    formatted_total_payable = format_currency(total_payable)
    formatted_value = format_currency(value)
    return total_payable, value, formatted_total_payable, formatted_value

def save_outcomes(data, csv_file_path, user_info, months_free, offer_bin, offer_str, value, total_payable):
    url = user_info['url']
    row_data = [
        user_info['registration'], months_free, offer_bin, offer_str,
        value, total_payable, user_info['total_annual_subs'], datetime.now(),
        url
    ]

    if 'intermediary' in url:
        intermediary = data['intermediary']
        intermediary_advisor = data['intermediary-advisor']
        row_data.extend([intermediary, intermediary_advisor])
    else:
        row_data.extend(['', ''])

    save_to_csv(csv_file_path, row_data)

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        user_data = request.json.get('user_data', {})
        outcomes_data = request.json.get('outcomes_data', {})
        url = request.headers.get('Referer')
        csv_file_path = os.path.join('data', db_schema_2)
        row_data = prepare_submission_data(user_data, outcomes_data, url)
        save_to_csv(csv_file_path, row_data)

        return jsonify({'message': 'Successfully submitted.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def prepare_submission_data(user_data, outcomes_data, url):
    base_row_data = [
        user_data.get('registration-number', ''),
        user_data.get('renewal-date', ''),
        user_data.get('annual-subs', ''),
        user_data.get('color-segment', ''),
        user_data.get('claims-paid', ''),
        user_data.get('payment-frequency', ''),
        user_data.get('months-arrears', ''),
        user_data.get('months-free-last', ''),
        user_data.get('months-free-this', ''),
        datetime.now(),
        url,
        outcomes_data.get('offer', ''),
        outcomes_data.get('offer-accepted', '')
    ]

    if 'intermediary' in url:
        base_row_data.extend([
            user_data.get('intermediary', ''),
            user_data.get('intermediary-advisor', '')
        ])
    else:
        base_row_data.extend(['', ''])

    return base_row_data

if __name__ == '__main__':
    app.run(debug=True)