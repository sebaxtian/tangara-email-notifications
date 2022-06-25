"""
    Update the sensors_status.csv for each sensor when is down or is up

    Run:
        python sensors_status.py -u -s input/sensors.csv
        python sensors_status.py --sensors_status --sensors input/sensors.csv
    
    Return:
        Dataframe with sensors status
"""
import sys
import pandas as pd
from optparse import OptionParser
from datetime import datetime, timezone, timedelta
from request_sensors import RequestSensors
from request_sensors import RequireOptions


def SetupOptionParser():
    # Usage message is the module's docstring.
    parser = OptionParser(usage=__doc__)
    parser.add_option("-u", "--sensors_status",
                      action="store_true",
                      dest="sensors_status",
                      help="Update the Output: sensors_status.csv for each sensor when is down or is up")
    parser.add_option("-s", "--sensors",
                      default=None,
                      help="Input: sensors.csv file that contains each Tangara sensor registered")
    return parser


def SensorsStatus(request_sensors):
    # Get Available Sensors
    available_sensors = request_sensors['available_sensors']
    # Get Unavailable Sensors
    unavailable_sensors = request_sensors['unavailable_sensors']

    # Load sensors status historically
    sensors_status = pd.read_csv('output/sensors_status.csv')

    # Current Datetime
    dt = datetime.now(timezone(timedelta(hours=-5))).isoformat()

    # Update Unavailable Sensors
    for index, row in unavailable_sensors.iterrows():
        last_report = sensors_status[sensors_status['SENSOR_ID'] == row['ID']].tail(
            1)
        if last_report.empty:
            sensors_status.loc[len(sensors_status)] = [
                dt, None, row['ID'], row['PERSON_IN_CHARGE_ID'], 0]
        else:
            if last_report['DATETIME_UP'].isna().values.any():
                sensors_status.loc[last_report.index,
                                   'ATTEMPTS'] = last_report['ATTEMPTS'] + 1
            else:
                sensors_status.loc[len(sensors_status)] = [
                    dt, None, row['ID'], row['PERSON_IN_CHARGE_ID'], 0]

    # Update Available Sensors
    for index, row in available_sensors.iterrows():
        last_report = sensors_status[sensors_status['SENSOR_ID'] == row['ID']].tail(
            1)
        if last_report.empty:
            sensors_status.loc[len(sensors_status)] = [
                None, dt, row['ID'], row['PERSON_IN_CHARGE_ID'], 0]
        else:
            if not last_report['DATETIME_DOWN'].isna().values.any() and last_report['DATETIME_UP'].isna().values.any():
                sensors_status.loc[last_report.index, 'DATETIME_UP'] = dt

    sensors_status.to_csv('output/sensors_status.csv', index=False)
    return sensors_status


def main(argv):
    options_parser = SetupOptionParser()
    (options, args) = options_parser.parse_args()
    #print("argv", argv, "options", options, "args", args)
    RequireOptions(options, 'sensors')

    # Get Sensors, Available Sensors and Unavailable Sensors
    request_sensors = RequestSensors(options.sensors)

    # Sensors Status
    SensorsStatus(request_sensors)


if __name__ == '__main__':
    main(sys.argv)
