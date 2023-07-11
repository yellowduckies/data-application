
# Data Application

This is a project submission to XVector Labs.
## Project URLs
 
 - [Assignment PDF](https://github.com/yellowduckies/data-application/blob/master/Project%20Specs.pdf)    
 - [Data Application XVector Labs live project link](http://3.7.68.98:5000/)


## API Reference

#### Get all datasets

```http
curl -X GET http://3.7.68.98:5000/dataset
```

| Description                |
|:------------------------- |
| Gives the list of stored data |

#### Upload a dataset

```http
curl -X POST -F "data_name=<string>" -F "file=@<path_to_your_file>" http://3.7.68.98:5000/dataset
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `data_name`      | `string` | **Required**, data_name will be the filename |
| `file`      | `file` | **Required**, will be stored |

#### Compute a dataset

```http
curl -X POST -F "column_name=<string>" -F "operation=<max/average/min/sum(string)>" http://3.7.68.98:5000/dataset/<int:dataset_id>/compute
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `dataset_id`      | `int` | **Required**, dataset will be searched using this dataset_id |
| `column_name`      | `string` | **Required**, to search for column in dataset |
| `operation`      | `string` | **Required**, to perform operation in backend and return the result |

#### Get Plot data from dataset

```http
curl -X GET http://3.7.68.98:5000/dataset/<int:dataset_id>/plot?column1=<column_1>&column2=<column_2>
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `dataset_id`      | `int` | **Required**, dataset will be searched using this dataset_id |
| `column1`      | `string` | **Required**, to get all the values of column1 from dataset |
| `column2`      | `string` | **Required**, to get all the values of column1 from dataset |

#### Note
The Plot data API will return data from column of upto 100 rows only.


## Installation

To run this project

#### Install all the project requirements
```bash
pip install -r requirements.txt
```

#### Environment Variables

Create a Database and create a .env file within the project directory and pass the values of

`DBNAME=<database name>`

`USER=<database username>`

`PASSWORD=<database user password>`

`HOST=<host address>`

`PORT=<port>`

`UPLOAD_FOLDER=./datasets`



#### Move to the project directory and use this command to run the code
```bash
python3 app.py
```
