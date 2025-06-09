import mlflow.models
import mlflow.sklearn
from airflow.sdk import dag, task
from airflow.models import Param
from airflow.sdk import Variable

import pandas as pd
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
import mlflow
import mlflow.sklearn

import pendulum
import os
import requests

REMOTE_URL = Variable.get("remote_url", default="https://d37ci6vzurychx.cloudfront.net/trip-data/")
DOWNLOAD_DIR = Variable.get("download_dir", default="/tmp/nyc-taxi-data")

@dag(
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    params={
        "taxi_type": Param("yellow", type="string", enum=["yellow", "green"]),
        "month": Param("2023-03", type="string")
    }
)
def mlops():

    @task
    def download_data(taxi_type: str, month: str):
        """
        Download NYC taxi trip data for a specific month and taxi type.
        Args:
            taxi_type (str): Type of taxi data to download ('yellow' or 'green').
            month (str): Month in the format 'YYYY-MM' for which to download data.
        Returns:
            str: Path to the downloaded file.
        """
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        file_name = f"{taxi_type}_tripdata_{month}.parquet"
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        url = f"{REMOTE_URL}{file_name}"

        # print(f"Downloading {file_name} from {url} to {file_path}")

        # response = requests.get(url)
        # if response.status_code == 200:
        #     with open(file_path, "wb") as f:
        #         f.write(response.content)
        #     print(f"Downloaded {file_name} to {file_path}")
        # else:
        #     raise Exception(f"Failed to download {file_name}. Status: {response.status_code}")
        return file_path
    
    @task
    def transform_train(file_path: str, taxi_type: str):
        """
        Transform the downloaded data file.
        Args:
            file_path (str): Path to the downloaded data file.
        Returns:
            pd.DataFrame: Transformed DataFrame.
        """
        print(f"Transforming data from {file_path}")
        df = pd.read_parquet(file_path)
        print(f"Data shape: {df.shape}")

        df['duration'] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
        df.duration = df.duration.dt.total_seconds() / 60

        df = df[(df.duration >= 1) & (df.duration <= 60)]

        categorical = ['PULocationID', 'DOLocationID']
        df[categorical] = df[categorical].astype(str)
        
        print(f"Transformed data shape: {df.shape}")

        numerical = ['trip_distance']

        dv = DictVectorizer()
        dicts = df[categorical + numerical].to_dict(orient='records')
        print(f"{dicts[:5]}")
        X = dv.fit_transform(dicts)
        y = df['duration'].values
        print(f"Training data shape: {X.shape}, Target shape: {y.shape}")

        mlflow.set_tracking_uri("file:///opt/airflow/mlruns")
        mlflow.set_experiment(f'nyc-{taxi_type}-taxi-experiment')
        lr = LinearRegression()

        with mlflow.start_run():
            mlflow.set_tag("model", "lr")
            mlflow.log_param("taxi_type", taxi_type)
            
            lr.fit(X, y)
            y_pred = lr.predict(X)

            rmse = root_mean_squared_error(y, y_pred)
            mlflow.log_metric("rmse", rmse)
            print(f"intercept: {lr.intercept_}")
            mlflow.sklearn.log_model(lr, artifact_path="model")
            # mlflow.log_artifact(file_path, artifact_path="data")


        client = mlflow.tracking.MlflowClient()

        experiment = client.get_experiment_by_name(f'nyc-{taxi_type}-taxi-experiment')
        last_run = client.search_runs(
            experiment_ids=experiment.experiment_id,
            max_results=1,
            order_by=["attributes.created DESC"]
        )[0]
        print(f"Last run ID: {last_run.info.run_id}")

        mlflow.register_model( 
        model_uri=f"runs:/{last_run.info.run_id}/model",
        name="LinearRegressionModel"
        )
    

    @task
    def cleanup(file_path: str):
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file {file_path}")
        else:
            print(f"File {file_path} not found during cleanup.")
    
    downloaded_file = download_data(taxi_type="{{ params.taxi_type }}", month="{{ params.month }}")
    transform_train(file_path=downloaded_file, taxi_type="{{ params.taxi_type }}")
    # cleanup(downloaded_file)



dag_mlops = mlops()