
import pickle
import pandas as pd

from flask import Flask, request, jsonify

with open('model.bin', 'rb') as f_in:
    dv, model = pickle.load(f_in)

categorical = ['PULocationID', 'DOLocationID']

def read_data(filename):
    df = pd.read_parquet(filename)

    df['duration'] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60

    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')

    return df



def run(taxi_type, year, month):
    # taxi_type = sys.argv[1]
    # year = sys.argv[2]
    # month = sys.argv[3]

    df = read_data(f"https://d37ci6vzurychx.cloudfront.net/trip-data/{taxi_type}_tripdata_{year}-{month}.parquet")

    dicts = df[categorical].to_dict(orient='records')
    X_val = dv.transform(dicts)
    y_pred = model.predict(X_val)

    df['ride_id'] = f'{year}/{month}_' + df.index.astype('str')

    df_result = pd.DataFrame()


    df_result['ride_id'] = df['ride_id']
    df_result['predicted_duration'] = y_pred

    output_file = f"./{taxi_type}/{year}-{month}.parquet"

    df_result.to_parquet(
        output_file,
        engine='pyarrow',
        compression=None,
        index=False
    )

    reslut ={
        "mean_duration": y_pred.mean(),
    }

    return jsonify(reslut)

app = Flask('my-predictor')

@app.route('/predict', methods=['POST'])
def my_endpoint():
    request_data = request.get_json()
    taxi_type = request_data['taxi_type']
    year = request_data['year']
    month = request_data['month']
    return run(taxi_type, year, month)

if __name__ == '__main__':
    app.run(host='localhost', port=9696, debug=True)








