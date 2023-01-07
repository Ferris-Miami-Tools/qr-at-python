# Packages that are included with Python - similar to math
import json
import os.path
# Packages that are not included with Python - I had to install these
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"] # uppercase because it is a constant
CLASSES = (
  ("08:15:00", "08:45:00", "09:50:00"),
  ("09:50:00", "10:20:00", "11:25:00"),
  ("11:25:00", "11:55:00", "13:00:00"),
  ("13:00:00", "13:30:00", "14:35:00"),
  ("14:35:00", "15:05:00", "16:10:00"),
  ("16:10:00", "16:40:00", "17:45:00"),
  ("17:45:00", "18:15:00", "19:20:00")
)

# This fucntion loads your name, email, and class time from a format known as json
def get_instructors():
  f = open("instructors.json")
  instructors = json.load(f)
  f.close()

  return [instructors["elnagar"], instructors["ferris"], instructors["houten"], instructors["palmisano"]]

def get_sheet(sheet_id, range):
  creds = None
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
      creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  
  if not creds or not creds.valid:
    raise Exception("Missing credentials.json file")

  service = build("sheets", "v4", credentials=creds)

  sheet = service.spreadsheets()
  result = sheet.values().get(spreadsheetId=sheet_id, range=range).execute()
  values = result.get("values", [])

  if not values:
    raise Exception("No records in Google Spreadsheet")
  else:
    df = pd.DataFrame(values[1:], columns=["timestamp", "email"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def df_between_ts(df, start, stop):
  return df[(df["timestamp"] >= start) & (df["timestamp"] < stop)]

def process_request(attendance, req_instructor, req_date, req_class):
  instructors = get_instructors()
  instructor = instructors[req_instructor]

  class_times = CLASSES[req_class]
  start_ts = req_date + " " + class_times[0]
  late_ts = req_date + " " + class_times[1]
  end_ts = req_date + " " + class_times[2]

  df_class = df_between_ts(attendance, start_ts, end_ts)
  df_late = df_between_ts(attendance, late_ts, end_ts)

  # Find late students
  # Below is a single line solution of lines 77-81
  # late = [instructor[t]["name"] for t in instructor if t in df_late["email"].tolist() and instructor[t]["classSlot"] == str(req_class)]
  late = []
  for t in instructor:
    if t in df_late["email"].tolist() and instructor[t]["classSlot"] == str(req_class):
      name_split = instructor[t]["name"].split(", ")
      late.append(name_split[1] + " " + name_split[0])
  
  # Find missing students
  # Below is a single line solution of lines 86-90
  # missing = [instructor[t]["name"] for t in instructor if t not in df_class["email"].tolist() and instructor[t]["classSlot"] == str(req_class)]
  missing = []
  for t in instructor:
    if t not in df_class["email"].tolist() and instructor[t]["classSlot"] == str(req_class):
      name_split = instructor[t]["name"].split(", ")
      missing.append(name_split[1] + " " + name_split[0])

  # Display the late and missing students
  print("LATE (" + str(len(late)) + ")")
  print(", ".join(late)) # rather than printing the list I convert the list to a string by joining the elements together with ", " between
  print("MISSING (" + str(len(missing)) + ")")
  print(", ".join(missing))

attendance = get_sheet("1Rmc1UWb7wyPdtPIb_Fa52wLPxjJhYDsQsuiWJZtLaOM", "Form Responses 1!A:E")
running = True
while running:
  print("QR @ - BUS104 Attendance Monitoring")
  search_date = input("Enter the date (e.g. 2021-10-01): ")
  print("Instructors: (0) Elnagar (1) Ferris (2) Van Houten (3) Palmisano")
  instructor = int(input("Enter the instructor id (e.g. 1): "))
  print("Class times: (0) 8:30 AM (1) 10:05 AM (2) 11:40 AM (3) 1:15 PM (4) 2:50 PM (5) 4:25 PM (6) 6:00")
  class_time = int(input("Enter the class time (e.g. 2): "))

  process_request(attendance, instructor, search_date, class_time)

  keep_running = input("Would you like to analyze another class (Y/N)? ")
  if keep_running.lower() == "n":
    print("Thank you for using QR @")
    running = False
  elif keep_running.lower() == "y":
    print("Continuing")
  else:
    print("Invalid input. Stopping the program. Thank you for using QR @")
