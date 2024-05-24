from flask import Flask, render_template, request, jsonify
import csv
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Route for handling form submission
@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        data = request.json

        # Extracting data from JSON
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

        # Writing data to CSV
        csv_file_path = os.path.join('data', 'user_data.csv')
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        with open(csv_file_path, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow([registration_number, renewal_date, annual_subs, color_segment, claims_paid, payment_frequency, months_arrears, months_free_last, months_free_this, offer_accepted])

        return jsonify({'message': 'Input saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# New route to multiply annual subs by 5 and save to CSV
@app.route('/multiply', methods=['POST'])
def multiply_annual_subs():
    try:
        data = request.json
        registration_number = data['registration-number']
        annual_subs = float(data['annual-subs'])
        result = annual_subs * 5
        url = data.get('url')  # Get the URL from the request data

        # Writing data to CSV
        csv_file_path = os.path.join('data', 'calculated_data.csv')
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        with open(csv_file_path, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow([registration_number, result, datetime.now(), url])  # Include URL in the CSV row
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
