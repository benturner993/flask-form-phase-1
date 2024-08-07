from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
from calculator import (calculate_months, calculate_value,
                        eligibility, format_currency)
from utils import save_to_csv

# make sure it works across the channels / pages
# how does this tie in with forms?

# static variables
schema = 'consumer_retention'
db_schema_searches = f'{schema}-searches.csv'
db_schema_outcomes = f'{schema}-outcomes.csv'

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
        months_free = calculate_months_free(user_info)
        offer_bin, offer_str = eligibility(months_free)
        total_payable, value, formatted_total_payable, formatted_value = calculate_financials(user_info, months_free)
        csv_file_path = os.path.join('data', db_schema_searches)

        row_data = [
            user_info['guid'],
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
            user_info['url'],
            months_free,
            offer_bin,
            offer_str,
            value,
            total_payable,
            datetime.now()
        ]

        if 'intermediary' in user_info['url']:
            intermediary = data['user-intermediary']
            intermediary_advisor = data['user-intermediary-advisor']
            row_data.extend([intermediary, intermediary_advisor])
        else:
            row_data.extend(['', ''])
        save_to_csv(csv_file_path, row_data)

        return jsonify({
            'result': offer_str,
            'eligible': offer_bin,
            'value': formatted_value,
            'total_payable': formatted_total_payable,
            'user_data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def calculate_months_free(user_info):
    return calculate_months(
        user_info['user-annual-subs'],
        user_info['registration-number'],
        user_info['user-months-arrears'],
        user_info['user-financial-distress'],
        user_info['user-months-free-last'],
        user_info['user-months-free-this'],
        user_info['user-color-segment'],
        user_info['user-claims-paid']
    )

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
        outcomes_data = request.json.get('outcomes_data', {})
        url = request.json.get('url')
        guid = request.json.get('guid')

        print('user_data:',user_data)
        print('outcomes_data:',outcomes_data)
        print('url:',url)
        print('guid:', guid)

        csv_file_path = os.path.join('data', db_schema_outcomes)

        base_row_data = [
            guid,
            user_data.get('registration-number', ''),
            user_data.get('user-renewal-date', ''),
            user_data.get('user-annual-subs', ''),
            user_data.get('user-color-segment', ''),
            # user_data.get('user-claims-paid', ''),
            # user_data.get('user-payment-frequency', ''),
            # user_data.get('user-months-arrears', ''),
            # user_data.get('user-months-free-last', ''),
            # user_data.get('user-months-free-this', ''),
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

        # row_data = prepare_submission_data(user_data, outcomes_data, url)
        save_to_csv(csv_file_path, base_row_data)

        return jsonify({'message': 'Successfully submitted.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)