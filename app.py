from flask import Flask, render_template, request, jsonify
import csv
import os
from datetime import datetime
from calculator import (calculate_months, calculate_value,
                        eligibility, format_currency)

# static variables
schema = 'consumer_retention'
db_schema_1 = f'{schema}-direct_outcomes.csv'
db_schema_2 = f'{schema}-direct_searches.csv'

app = Flask(__name__)

def save_to_csv(file_path, row_data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(row_data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/direct')
def direct():
    return render_template('direct.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        data = request.json

        registration_number = data['registration-number']
        renewal_date = data['renewal-date']
        annual_subs = data['annual-subs']
        color_segment = data['color-segment']
        claims_paid = data['claims-paid']
        payment_frequency = data['payment-frequency']
        months_arrears = data['months-arrears']
        months_free_last = data['months-free-last']
        months_free_this = data['months-free-this']
        offer_accepted = data['offer-accepted']

        csv_file_path = os.path.join('data', db_schema_1)
        row_data = [registration_number, renewal_date, annual_subs, color_segment, claims_paid, payment_frequency, months_arrears, months_free_last, months_free_this, offer_accepted, datetime.now()]
        save_to_csv(csv_file_path, row_data)

        return jsonify({'message': 'Successfully submitted.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/calculate_offer', methods=['POST'])
def calculate_offer():
    try:
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
        csv_file_path = os.path.join('data', db_schema_2)
        row_data = [registration, months_free, offer_bin, offer_str, value, total_payable, total_annual_subs, datetime.now(), url]
        save_to_csv(csv_file_path, row_data)

        return jsonify({'result': offer_str, 'eligible': offer_bin, 'value': formatted_value, 'total_payable': formatted_total_payable})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)