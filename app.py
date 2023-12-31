from flask import Flask, request, render_template
from flask_restful import Api, Resource
from werkzeug.utils import secure_filename
import psycopg2
import traceback
import os
import csv
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
api = Api(app)

# Database connection configuration
app.config['DATABASE'] = {
    'dbname': os.getenv('DBNAME'),
    'user': os.getenv('USER'),
    'password': os.getenv('PASSWORD'),
    'host': os.getenv('HOST'),
    'port': os.getenv('PORT')
}
upload_folder = os.getenv('UPLOAD_FOLDER')

def get_db_connection():
    """Helper function to establish a database connection"""
    conn = psycopg2.connect(
        dbname=app.config['DATABASE']['dbname'],
        user=app.config['DATABASE']['user'],
        password=app.config['DATABASE']['password'],
        host=app.config['DATABASE']['host'],
        port=app.config['DATABASE']['port']
    )
    return conn


class DatasetResource(Resource):
    """Resource for the /dataset API"""
    def get(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Retrieve the list of stored datasets
            cursor.execute("SELECT * FROM datasets ORDER BY id DESC")
            dataset_names = cursor.fetchall()
            if len(dataset_names) > 0:
                return dataset_names, 200
            else:
                return {'error': 'No datasets found'}, 400
        except Exception as e:
            traceback.print_exc()
            return {'error': 'An error occurred while retrieving dataset list.'}, 500
        finally:
            cursor.close()
            conn.close()

    def post(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        data_name = request.form['data_name']

        if 'file' not in request.files:
            return {'error': 'No file part in the request.'}, 400

        csv_file = request.files['file']

        if csv_file.filename == '':
            return {'error': 'No file selected.'}, 400

        try:
            # Save the CSV file
            csv_filename = f'{upload_folder}/{secure_filename(data_name)}.csv'
            count = 1
            while os.path.exists(csv_filename):
                csv_filename = f'{upload_folder}/{secure_filename(data_name)}_{count}.csv'
                count += 1
            csv_file.save(csv_filename)

            # Insert dataset information into the database
            cursor.execute(
                "INSERT INTO datasets (data_name, file_path) VALUES (%s, %s)", (data_name, csv_filename))
            conn.commit()

            return {'message': 'Dataset uploaded successfully.'}, 201
        except Exception as e:
            traceback.print_exc()
            conn.rollback()
            return {'error': 'An error occurred while uploading the dataset.'}, 500

class GetColumnResource(Resource):
    """Resource for the /dataset/:id API"""
    def get(self, dataset_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        only_integer = request.args.get('only_integer', False)
        try:
            # Retrieve the dataset
            cursor.execute(
                "SELECT * FROM datasets WHERE id = %s", (dataset_id,))
            dataset = cursor.fetchone()
            if dataset is None:
                return {'error': 'No datasets found'}, 400

            file_path = dataset[2]
            result_dict = {}
            # Open the CSV file and perform the operation
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames

                for column_name in fieldnames:
                    result_dict[column_name] = []

                for row in reader:
                    for column_name in fieldnames:
                        value = row[column_name]
                        if only_integer:
                            try:
                                value = int(value)
                            except ValueError:
                                pass
                            result_dict[column_name].append(value)
                        else:
                            result_dict[column_name].append(value)

            keys = []
            for key, values in result_dict.items():
                if only_integer:
                    if all(isinstance(value, int) for value in values):
                        keys.append(key)
                else:
                    keys.append(key)

            return keys

        except Exception as e:
            traceback.print_exc()
            return {'error': 'An error occurred while retrieving dataset list.'}, 500
        finally:
            cursor.close()
            conn.close()


class ComputeResource(Resource):
    """Resource for the /dataset/:id/compute API"""
    def post(self, dataset_id):
        conn = get_db_connection()
        cursor = conn.cursor()

        column_name = request.form['column_name']
        operation = request.form['operation']

        try:
            # Retrieve the dataset from the database
            cursor.execute(
                "SELECT * FROM datasets WHERE id = %s", (dataset_id,))
            dataset = cursor.fetchone()

            if dataset is None:
                return {'error': 'Dataset not found.'}, 404

            file_path = dataset[2]
            # Open the CSV file and perform the operation
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                values = [float(row[column_name]) for row in reader]

                if operation == 'sum':
                    result = sum(values)
                elif operation == 'max':
                    result = max(values)
                elif operation == 'average':
                    result = sum(values) / len(values)
                elif operation == 'min':
                    result = min(values)
                else:
                    return {'error': 'Invalid operation specified.'}, 400

            return {'result': result}, 200

        except Exception as e:
            traceback.print_exc()
            return {'error': 'An error occurred while performing the operation.'}, 500
        finally:
            cursor.close()
            conn.close()

class PlotResource(Resource):
    """Resource for the /dataset/:id/plot API"""
    def get(self, dataset_id):
        column1 = request.args.get('column1')
        column2 = request.args.get('column2')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Retrieve the dataset from the database
            cursor.execute(
                "SELECT * FROM datasets WHERE id = %s", (dataset_id,))
            dataset = cursor.fetchone()

            if dataset is None:
                return {'error': 'Dataset not found.'}, 404

            file_path = dataset[2]

            # Read the CSV file and extract the data
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                data = list(reader)

                if len(data)>100:
                    data = data[:100]

                # Get the first 25-30 values of the specified columns
                values1 = [row[column1] for row in data]
                values2 = [row[column2] for row in data]

            # Prepare the JSON data
            plot_data = {column1: values1, column2: values2}

            return plot_data, 200

        except Exception as e:
            traceback.print_exc()
            return {'error': 'An error occurred while retrieving the plot data.'}, 500

        finally:
            cursor.close()
            conn.close()


# Add the DatasetResource to the API
"""To post a new dataset / To get the list of all datasets"""
api.add_resource(DatasetResource, '/dataset/')

"""To the columns of selected dataset"""
api.add_resource(GetColumnResource, '/dataset/<int:dataset_id>/get_columns/')

"""To compute operations like: max, min, sum and average"""
api.add_resource(ComputeResource, '/dataset/<int:dataset_id>/compute/')

"""To fetch all the values of columns for data ploting"""
api.add_resource(PlotResource, '/dataset/<int:dataset_id>/plot/')


@app.route('/')
def index():
    return render_template('base.html')

if __name__ == '__main__':
    """Run the Flask application"""
    # Check if the required environment variables are set
    required_env_vars = ['DBNAME', 'USER',
                         'PASSWORD', 'HOST', 'PORT', 'UPLOAD_FOLDER']
    missing_env_vars = [
        env_var for env_var in required_env_vars if os.getenv(env_var) is None]
    if missing_env_vars:
        print(
            f"Missing required environment variables: {', '.join(missing_env_vars)}")
        exit(1)

    app.run(debug=True)
