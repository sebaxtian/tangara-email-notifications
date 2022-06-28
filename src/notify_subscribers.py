"""
    Email notification to subscribers when any sensor is down

    Run:
        python notify_subscribers.py -n -s ../input/sensors.csv
        python notify_subscribers.py --notify_subscribers --sensors ../input/sensors.csv
    
    Return:
        Message object, including message id
"""
import sys
import os
import base64
import pandas as pd
from optparse import OptionParser
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.message import EmailMessage
from request_sensors import RequireOptions
from request_sensors import RequestSensors
from sensors_status import SensorsStatus

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# OR, the same with increased verbosity
# load_dotenv(verbose=True)

# OR, explicitly providing path to '.env'
# python3 only
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


# Gmail API Credentials
CREDENTIALS = None


def SetupOptionParser():
    # Usage message is the module's docstring.
    parser = OptionParser(usage=__doc__)
    parser.add_option("-n", "--notify_subscribers",
                      action="store_true",
                      dest="notify_subscribers",
                      help="Email notification to subscribers when any sensor is down")
    parser.add_option("-s", "--sensors",
                      default=None,
                      help="Input: sensors.csv file that contains each Tangara sensor registered")
    return parser


def _Load_Credentials():
    # Credentials
    global CREDENTIALS
    if CREDENTIALS:
        return CREDENTIALS
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    TOKEN_URI = "https://oauth2.googleapis.com/token"
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    TOKEN = os.getenv("TOKEN")
    REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
    # Credentials
    CREDENTIALS = Credentials(token=TOKEN, refresh_token=REFRESH_TOKEN, token_uri=TOKEN_URI,
                              client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=SCOPES)
    return CREDENTIALS


def _GetCredentials():
    # If there are no (valid) credentials available, let the user log in.
    creds = _Load_Credentials()
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("Refresh Credentials")
        else:
            # Please run Get Credentials from Client Secrets File
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', creds.scopes)
            creds = flow.run_local_server(port=0)
            print("Please run Get Credentials from Client Secrets File")
    # Credentials
    return creds


def _SentEmailNotification(strfrom, strto, strsubject, strmessage):
    """
        Create and send an email message
        Print the returned  message id
        Returns: Message object, including message id

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
    """
    try:
        service = build('gmail', 'v1', credentials=_GetCredentials())
        message = EmailMessage()

        # Founders Emails to sent the message to Bcc
        FOUNDERS_EMAILS = ','.join(os.getenv("FOUNDERS_EMAILS").split(','))

        message['From'] = strfrom
        message['To'] = strto
        message['Bcc'] = FOUNDERS_EMAILS
        message['Subject'] = strsubject

        message.set_content(strmessage)

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
            .decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = service.users().messages().send(userId="me", body=create_message)
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message


def _EmailNotification(request_id, response, exception):
    """Do something with the email notification response."""
    if exception is not None:
        # Do something with the exception.
        print(F'An error occurred: {exception}')
    else:
        # Do something with the response.
        print(F'Message ID: {response["id"]}, Request ID: {request_id}')


def NotifySubscribers(sensors_status, sensors):
    THRESHOLD_ATTEMPTS = int(os.getenv("THRESHOLD_ATTEMPTS"))
    # Get down sensors only
    down_sensors = sensors_status[(~sensors_status['DATETIME_DOWN'].isna()) & (
        sensors_status['DATETIME_UP'].isna()) & ((sensors_status['ATTEMPTS'] % THRESHOLD_ATTEMPTS) == 0)]

    # Load people in charge
    people_in_charge = pd.read_csv('input/mailing_list.csv')

    # Join down sensors and people in charge
    down_sensors = down_sensors.set_index(
        'PERSON_IN_CHARGE_ID').join(people_in_charge.set_index('ID'))

    # Join down sensors and sensors
    down_sensors = down_sensors.set_index(
        'SENSOR_ID').join(sensors.set_index('ID'))

    # Service to send emails notifications from batch
    service = build('gmail', 'v1', credentials=_GetCredentials())
    batch = service.new_batch_http_request(callback=_EmailNotification)

    # Sent Email Notifications
    for index, row in down_sensors.iterrows():
        subject = f"Sensor Tangara: {row['NAME']}"

        """
        @TODO: Create a new personalized message by person
               Create a new Gmail API for Tangara Google Account
        strfrom = "sebaxtianrioss@gmail.com"
        strto = f"{row['EMAIL']}"
        message = f"Hola {row['FIRST_NAME']} {row['LAST_NAME']}, el sensor de Tangara: {row['NAME']} no se encuentra reportando datos desde la fecha: {row['DATETIME_DOWN']}.\n"\
            "Por favor apague y vuelva a encender el sensor, si el problema persiste, comuniquese con el equipo de Tangara, Gracias."
        """

        message = f"Hola, el sensor de Tangara: {row['NAME']} no está reportando datos desde la fecha: {row['DATETIME_DOWN']}.\n" \
            "Por favor apague y vuelva a encender el sensor, verifique que funcione el internet en el lugar.\n" \
            "Si el problema persiste, comuniquese con el equipo de Tangara:\n" \
            "Grupo en WhatsApp: https://chat.whatsapp.com/ITyQlokTiBMGrRAfuXVT0j\n" \
            "Gracias."

        # Sent Email Notification
        send_message = _SentEmailNotification(
            "sebaxtianrioss@gmail.com", f"{row['EMAIL']}", subject, message)
        # Add request to batch
        batch.add(request_id=f"{row['NAME']}", request=send_message)

    # Execute Email Notifications from Batch
    batch.execute()


def main(argv):
    options_parser = SetupOptionParser()
    (options, args) = options_parser.parse_args()
    #print("argv", argv, "options", options, "args", args)
    RequireOptions(options, 'sensors')

    # Get Sensors, Available Sensors and Unavailable Sensors
    request_sensors = RequestSensors(options.sensors)

    # Sensors Status
    sensors_status = SensorsStatus(request_sensors)

    # Notify Subscribers
    NotifySubscribers(sensors_status, request_sensors['sensors'])


if __name__ == '__main__':
    main(sys.argv)
