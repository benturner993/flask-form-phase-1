from flask import Flask, render_template, request, jsonify
# from flask_azure_oauth import FlaskAzureOAuth
import os
from datetime import datetime
from calculator import (calculate_months, calculate_value,
                        eligibility, format_currency)
from utils import save_to_csv

# static variables
schema = 'consumer_retention'
db_schema_1 = f'{schema}-direct_searches.csv'
db_schema_2 = f'{schema}-direct_outcomes.csv'

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
        # collect user information
        # user_info = request.oauth.user
        # username = user_info.get('name')
        # email = user_info.get('email')

        # collect input information
        data = request.json
        registration = float(data['registration-number'])
        renewal = datetime.strptime(data['renewal-date'], '%Y-%m-%d')
        payment_frequency = data['payment-frequency']
        total_annual_subs = float(data['annual-subs'])
        arrears = float(data['months-arrears'])
        financial_distress = 0
        mf_last_year = str(data['months-free-last'])
        mf_this_year = float(data['months-free-this'])
        segment = str(data['color-segment'])
        claims_paid = str(data['claims-paid'])
        url = data.get('url')

        # calculator number of eligible months free
        months_free = calculate_months(total_annual_subs,
                                  registration,
                                  arrears,
                                  financial_distress,
                                  mf_last_year,
                                  mf_this_year,
                                  segment,
                                  claims_paid)

        # return eligibility (offer_bin), and the written output (offer_str)
        offer_bin, offer_str = eligibility(months_free)

        # calculate the total payable amount and the value of the discount
        total_payable = calculate_value(total_annual_subs, payment_frequency, renewal, months_free)
        value = total_annual_subs - total_payable

        # Format the financial values
        formatted_total_payable = format_currency(total_payable)
        formatted_value = format_currency(value)

        # store outcomes and return
        csv_file_path = os.path.join('data', db_schema_1)
        row_data = [registration, months_free, offer_bin, offer_str, value, total_payable, total_annual_subs, datetime.now(), url]
        save_to_csv(csv_file_path, row_data)

        return jsonify({'result': offer_str, 'eligible': offer_bin, 'value': formatted_value, 'total_payable': formatted_total_payable, 'user_data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        # collect user information
        # collect user information
        # user_info = request.oauth.user
        # username = user_info.get('name')
        # email = user_info.get('email')

        # load the user form data and outcomes data
        user_data = request.json.get('user_data', {})
        outcomes_data = request.json.get('outcomes_data', {})

        # Get the URL from the request headers
        url = request.headers.get('Referer')

        # Save user data
        csv_file_path = os.path.join('data', db_schema_2)
        row_data = [user_data.get('registration-number', ''),
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
                    outcomes_data.get('offer-accepted', '')]
        save_to_csv(csv_file_path, row_data)

        return jsonify({'message': 'Successfully submitted.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)