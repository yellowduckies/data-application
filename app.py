from flask import Flask, request, render_template
from flask_restful import Api, Resource
from werkzeug.utils import secure_filename
import psycopg2
import traceback
import os, csv
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

# Helper function to establish a database connection
def get_db_connection():
    conn = psycopg2.connect(
        dbname=app.config['DATABASE']['dbname'],
        user=app.config['DATABASE']['user'],
        password=app.config['DATABASE']['password'],
        host=app.config['DATABASE']['host'],
        port=app.config['DATABASE']['port']
    )
    return conn


# Resource for the /dataset API
class DatasetResource(Resource):
    def get(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Retrieve the list of stored datasets
            cursor.execute("SELECT * FROM datasets")
            dataset_names = cursor.fetchall()
            if len(dataset_names)>0:
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
            cursor.execute("INSERT INTO datasets (data_name, file_path) VALUES (%s, %s)", (data_name, csv_filename))
            conn.commit()

            return {'message': 'Dataset uploaded successfully.'}, 201
        except Exception as e:
            traceback.print_exc()
            conn.rollback()
            return {'error': 'An error occurred while uploading the dataset.'}, 500

# Resource for the /dataset/:id/compute API
class ComputeResource(Resource):
    def post(self, dataset_id):
        conn = get_db_connection()
        cursor = conn.cursor()

        column_name = request.form['column_name']
        operation = request.form['operation']

        try:
            # Retrieve the dataset from the database
            cursor.execute("SELECT * FROM datasets WHERE id = %s", (dataset_id,))
            dataset = cursor.fetchone()

            if dataset is None:
                return {'error': 'Dataset not found.'}, 404

            file_path = dataset[2]
            # Open the CSV file and perform the operation
            with open(file_path, 'r') as csv_file:
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

# Resource for the /dataset/:id/plot API
class PlotResource(Resource):
    def get(self, dataset_id):
        column1 = request.form['column1']
        column2 = request.form['column2']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Retrieve the dataset from the database
            cursor.execute("SELECT * FROM datasets WHERE id = %s", (dataset_id,))
            dataset = cursor.fetchone()

            if dataset is None:
                return {'error': 'Dataset not found.'}, 404

            file_path = dataset[2]

            # Read the CSV file and extract the data
            with open(file_path, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                data = list(reader)

                # Get the first 25-30 values of the specified columns
                values1 = [float(row[column1]) for row in data]
                values2 = [float(row[column2]) for row in data]

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
api.add_resource(DatasetResource, '/dataset/') #To post a new dataset / To get the list of all datasets
api.add_resource(ComputeResource, '/dataset/<int:dataset_id>/compute/') #To compute operations like: max, min, sum and average
api.add_resource(PlotResource, '/dataset/<int:dataset_id>/plot') #To fetch all the values of columns for data ploting

@app.route('/')
def index():
    return render_template('base.html')

# Run the Flask application
if __name__ == '__main__':
    # Check if the required environment variables are set
    required_env_vars = ['DBNAME', 'USER', 'PASSWORD', 'HOST', 'PORT', 'UPLOAD_FOLDER']
    missing_env_vars = [env_var for env_var in required_env_vars if os.getenv(env_var) is None]
    if missing_env_vars:
        print(f"Missing required environment variables: {', '.join(missing_env_vars)}")
        exit(1)

    app.run(debug=True)
