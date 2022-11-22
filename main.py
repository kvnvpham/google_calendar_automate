from __future__ import print_function

import datetime
import csv
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.environ.get("CALENDAR_ID")
COMPANY = os.environ.get("COMPANY")


def credentials():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        return build('calendar', 'v3', credentials=creds)

    except HttpError as error:
        print("An error occurred: %s" % error)


def convert_date(date):
    fmt_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    return fmt_date


def convert_time(time):
    fmt_time = datetime.datetime.strptime(time, "%I:%M %p").time()
    return fmt_time


service = credentials()

schedule = []
with open("schedule.csv", newline='') as file:
    data = csv.DictReader(file)
    for row in data:
        date = row["Date"]
        start_time = convert_time(row["Start Time"])
        end_date = row["Date"]
        end_time = convert_time(row["End Time"])

        if convert_time("12:00 AM") <= end_time < convert_time("7:00 AM"):
            end_date = convert_date(date) + datetime.timedelta(days=1)
#
        schedule.append(
            {
                "date": date,
                "start_time": str(start_time),
                "end_date": str(end_date),
                "end_time": str(end_time)
            }
        )

for shift in schedule:
    event = {
        "summary": COMPANY,
        "start": {
            "dateTime": f"{shift['date']}T{shift['start_time']}",
            "timeZone": "America/Chicago",
        },
        "end": {
            "dateTime": f"{shift['end_date']}T{shift['end_time']}",
            "timeZone": "America/Chicago"
        }
    }

    event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print("Event created: %s" % (event.get('htmlLink')))
