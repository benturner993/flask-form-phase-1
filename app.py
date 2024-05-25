from flask import Flask, render_template, request, jsonify
import csv
import os
from datetime import datetime
from calculator import calculate

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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

        csv_file_path = os.path.join('data', 'user_data.csv')
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        with open(csv_file_path, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow([registration_number, renewal_date, annual_subs, color_segment, claims_paid, payment_frequency, months_arrears, months_free_last, months_free_this, offer_accepted])

        return jsonify({'message': 'Input saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/multiply', methods=['POST'])
def multiply_annual_subs():
    try:
        data = request.json

        total_annual_subs = float(data['annual-subs'])
        registration = float(data['registration-number'])
        arrears = float(data['months-arrears'])
        financial_distress = 0
        mf_last_year = str(data['months-free-last'])
        mf_this_year = float(data['months-free-this'])
        segment = str(data['color-segment'])
        claims_paid = str(data['claims-paid'])

        result = calculate(total_annual_subs,
                           registration,
                           arrears,
                           financial_distress,
                           mf_last_year,
                           mf_this_year,
                           segment,
                           claims_paid)
        url = data.get('url')

        csv_file_path = os.path.join('data', 'calculated_data.csv')
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        with open(csv_file_path, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow([registration, result, datetime.now(), url])
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
