from flask import Flask, render_template, request, send_file, session, redirect, url_for
import numpy as np
import csv
from io import StringIO
import json
from tempfile import NamedTemporaryFile
from flask_files import app
from flask_files.high_multiplicity_fair_allocation import high_multiplicity_fair_allocation
from fairpyx import Instance, AllocationBuilder, divide


def process_allocation(agent_capacities, item_capacities, valuations):
    """
    Processes the allocation of items to agents based on their capacities and valuations.

    Parameters:
    - agent_capacities (dict): The capacities of agents.
    - item_capacities (dict): The capacities of items.
    - valuations (dict): The valuations of agents for the items.

    Returns:
    - allocation (dict): The allocation of items to agents.
    """

    # Create an instance of the problem
    instance = Instance(agent_capacities=agent_capacities, item_capacities=item_capacities, valuations=valuations)

    # Use the allocation algorithm to find the allocation
    allocation = divide(high_multiplicity_fair_allocation, instance=instance)

    return allocation


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        agent_capacities_str = request.form.get('agent_capacities')
        item_capacities_str = request.form.get('item_capacities')
        valuations_str = request.form.get('valuations')

        if agent_capacities_str and item_capacities_str and valuations_str:
            try:
                agent_capacities = eval(agent_capacities_str)
                item_capacities = eval(item_capacities_str)
                valuations = eval(valuations_str)

                # Process the data using the high_multiplicity_fair_allocation algorithm
                allocation = process_allocation(agent_capacities, item_capacities, valuations)

                result = {
                    "agent_capacities": agent_capacities,
                    "item_capacities": item_capacities,
                    "valuations": valuations,
                    # "allocation": allocation
                    "allocation": None  # just now for the code to run
                }

                return render_template('result.html', result=result)

            except Exception as e:
                return render_template('input.html', error_message='Error processing input data: {}'.format(str(e)))

        else:
            return render_template('input.html', error_message='Please provide all required fields')


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        try:
            file = request.files['csv_file']
            if file:
                # Read CSV file
                stream = StringIO(file.stream.read().decode("UTF-8"))
                csv_input = csv.DictReader(stream)

                results = []
                for row in csv_input:
                    agent_capacities = json.loads(row.get('agent_capacities', '{}'))
                    item_capacities = json.loads(row.get('item_capacities', '{}'))
                    valuations = json.loads(row.get('valuations', '{}'))

                    if agent_capacities and item_capacities and valuations:
                        # Process allocation
                        allocation = process_allocation(agent_capacities, item_capacities, valuations)
                        results.append(allocation)
                    else:
                        break  # Exit the loop if any of the required fields is missing

                if results:
                    # Prepare output CSV file
                    output_csv = StringIO()
                    writer = csv.writer(output_csv)
                    writer.writerow(['Allocation'])

                    for allocation in results:
                        writer.writerow([json.dumps(allocation)])

                    output_csv.seek(0)

                    # Store output CSV in a temporary file
                    temp_file = NamedTemporaryFile(delete=False, mode='w+', newline='')
                    temp_file.write(output_csv.getvalue())
                    temp_file.close()

                    # Store the temporary file path in session
                    session['output_csv_path'] = temp_file.name

                    # Redirect to a new page where user can download the output CSV file
                    return redirect(url_for('result_csv'))

                else:
                    return render_template('index.html', error_message='No valid data found in CSV file.')

        except Exception as e:
            error_message = f"Error processing CSV file: {str(e)}"
            return render_template('index.html', error_message=error_message)

    return render_template('index.html')


@app.route('/result_csv')
def result_csv():
    # Retrieve the output CSV path from session
    output_csv_path = session.get('output_csv_path', None)
    if output_csv_path:
        with open(output_csv_path, 'r', newline='') as file:
            csv_reader = csv.DictReader(file)
            output_csv = [row for row in csv_reader]
        return render_template('result_csv.html', output_csv=output_csv)
    else:
        return render_template('index.html', error_message='No output CSV file found')


@app.route('/download')
def download():
    # Retrieve the output CSV path from session
    output_csv_path = session.get('output_csv_path', None)
    if output_csv_path:
        # Prepare response for download
        return send_file(
            output_csv_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name='output.csv'  # Provide a download name for the file
        )
    else:
        return render_template('index.html', error_message='No output CSV file found')


if __name__ == '__main__':
    app.run(debug=True)
