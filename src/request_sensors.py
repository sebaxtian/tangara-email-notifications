"""
    Request to InfluxDB API REST
    Get available sensors from InfluxDB

    Run:
        python request_sensors.py -r -s input/sensors.csv
        python request_sensors.py --request_sensors --sensors input/sensors.csv
    
    Return:
        Dict with Sensors, Available Sensors, and Unavailable Sensors from InfluxDB, both are Dataframes
        {
            'sensors': Dataframe,
            'available_sensors': Dataframe,
            'unavailable_sensors': Dataframe
        }
"""
import requests
import sys
import os
import pandas as pd
from optparse import OptionParser
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# OR, the same with increased verbosity
# load_dotenv(verbose=True)

# OR, explicitly providing path to '.env'
# python3 only
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


def SetupOptionParser():
    # Usage message is the module's docstring.
    parser = OptionParser(usage=__doc__)
    parser.add_option("-r", "--request_sensors",
                      action="store_true",
                      dest="available_sensors",
                      help="Get available sensors from InfluxDB")
    parser.add_option("-s", "--sensors",
                      default=None,
                      help="Input: sensors.csv file that contains each Tangara sensor registered")
    return parser


def RequireOptions(options, *args):
    missing = [arg for arg in args if getattr(options, arg) is None]
    if missing:
        print(f"Missing options: {' '.join(missing)}")
        sys.exit(-1)


def RequestSensors(csvfile):
    # Load Sensors
    sensors = pd.read_csv(csvfile)
    print("Total Sensors:", sensors.shape[0])

    ENDPOINT_INFLUXDB = os.getenv("ENDPOINT_INFLUXDB")
    DB_INFLUXDB = os.getenv("DB_INFLUXDB")
    THRESHOLD_MINUTES = os.getenv("THRESHOLD_MINUTES")

    # Create SQL sentence foreach sensor
    sensors['SELECT'] = sensors['MAC'].transform(
        lambda mac: f"SELECT \"name\", last(\"pm25\") FROM \"fixed_stations_01\" WHERE (\"name\" = '{mac}') AND time >= now() - {THRESHOLD_MINUTES}m and time <= now() GROUP BY time(30s) fill(none);")

    parameters = {
        'db': DB_INFLUXDB,
        'q': ''.join(sensors['SELECT'].values),
    }

    # Create GET request to InfluxDB
    response = requests.get(ENDPOINT_INFLUXDB, params=parameters)
    sensors.drop('SELECT', axis=1, inplace=True)

    # From results get the InfluxDB Sensors availables
    results = response.json()['results']
    results = [value for value in results if 'series' in value]

    available_sensors = pd.DataFrame()
    unavailable_sensors = pd.DataFrame()

    if len(results) > 0:
        influxdb_sensors = list(pd.json_normalize(results, record_path=[
                                'series', 'values']).sort_values(by=[0]).groupby(by=1).groups.keys())
        available_sensors = pd.DataFrame(data={'MAC': influxdb_sensors})

        # Filter only Available Sensors
        available_sensors = sensors[sensors['MAC'].isin(
            available_sensors['MAC'])]

        # Filter only Unavailable Sensors
        unavailable_sensors = sensors[~sensors['MAC'].isin(
            available_sensors['MAC'])]

    print('Total Available Sensors:', available_sensors.shape[0])
    print('Total Unavailable Sensors: ', unavailable_sensors.shape[0])

    return {'sensors': sensors, 'available_sensors': available_sensors, 'unavailable_sensors': unavailable_sensors}


def main(argv):
    options_parser = SetupOptionParser()
    (options, args) = options_parser.parse_args()
    #print("argv", argv, "options", options, "args", args)
    RequireOptions(options, 'sensors')

    # Request Available Sensors
    RequestSensors(options.sensors)


if __name__ == '__main__':
    main(sys.argv)
