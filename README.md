# tangara-email-notifications

Email notifications related to Tangara Sensors, when any sensor doesn't report data or isn't available.

---

## Requirements

- **Python 3**:
  - See [requirements.txt](./requirements.txt) file.

- **Gmail API Credentials**:
  - Please follow the official instructions to get the **credentials.json** file, this one has a JSON structure similar to the [example.credentials.json](./example.credentials.json) file.
    - See [https://developers.google.com/gmail/api/quickstart/python](https://developers.google.com/gmail/api/quickstart/python)
      ***The credentials.json file must be ignored from the repository***
  - **Refresh Token**:
    - This is a **token.json** file created when the script is first to run, this one has a JSON structure similar to the [example.token.json](./example.token.json) file, this file will be used to refresh the Gmail API token.
      ***The token.json file must be ignored from the repository***

## Environment Variables

Setup your own values to environment variables, use the [example.env](./example.env) file, and save your custom values as a **.env** file.
***The .env file must be ignored from the repository***

## Source Code

See [./src](./src) directory.

## Inputs

There are a couple of inputs to the Email Notifications, use the **mailing_list.csv** file to subscribe people that will be notified, They will be the people in charge of any Tangara sensor, and use the [sensors.csv](./sensors.csv) file to register each Tangara sensor.
Please use the [example.mailing_list.csv](./example.mailing_list.csv) to create the mailing_list.csv file.
***The mailing_list.csv file must be ignored from the repository***

## Outputs

Here is the [sensors_status.csv](./sensors_status.csv) file, this dataset contains the report about when each Tangara sensor was down or is up.

### How to use

Please read and execute each step below:

#### Step 1

Create and use Python virtual environment:

```bash
$promt> python -m venv .venv
$promt> source .venv/bin/activate
```

#### Step 2

Install all Python requirements:

```bash
$promt> python -m pip install -U pip
$promt> pip install -r requirements.txt
```

#### Step 3

Run Email Notifications Script:

```bash
$promt> python src/notify_subscribers.py -n -s input/sensors.csv
```

#### Optional

Generate a requirements file and then install from it in another environment:

```bash
$promt> pip freeze > requirements.txt
```

---

***That's all for now ...***

---

#### License

[GPL-3.0 License](./LICENSE)

#### About me

[https://about.me/sebaxtian](https://about.me/sebaxtian)
