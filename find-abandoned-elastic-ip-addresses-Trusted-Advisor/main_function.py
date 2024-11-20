# To execute this script, it is necessary to specify the environments
# 1. List of account and Rols ACCOUNTS = [{'name':'account_1', 'role_arn': 'arn:aws:iam::111111111111:role/role-assumed-by-main-acc'}, {'name':'account_2', 'role_arn': 'arn:aws:iam::222222222222:role/role-assumed-by-main-acc'}]
# where key - "name" consist name of observed account
# "role_arn" key: The ARN of the role in that account that has permissions to execute actions for gathering data from the observed account.
# 2. Credentials for access Google Sheet
# 3. WORKSHEETS_NAME = {'eip': 'Elastic IPs'} - reflect tab name in tables
# 4 SPREADSHEET_KEY = Spreadsheet_Key
# How to find your Google Spreadsheet Key https://www.appsadmins.com/blog/use-data-from-other-google-spreadsheets
# 5. Other data required for the authorization process

import boto3
from json import dumps
from json import loads
from httplib2 import Http
from datetime import datetime, timedelta
import hvac
from os import getenv
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.credentials import Credentials

#-----------------------------------------------------------------
def lambda_handler(event, context):
    # TODO implement
    req=get_checks()
    return {
        'statusCode': 200,
        'body': 'ok'
    }

#-----GET-SECRET-FOR-GOOGLE-SHEET-FROM-VAULT------------------------
def get_secrets(role):
#=========================
#
#Get the credentials or tokens for the place where you are going to publish the obtained results
#In that case, Vault was used
#
#=========================
    return secrets['data']['data']['token']

#----------------------MAIN-FUNCTION---------------------------------
def get_checks():
    #Data for get google autrh creds
    VAULT_ROLE = getenv("VAULT_ROLE")
    #Data for get accounts and push to google table
    ACCOUNTS = eval(os.environ['ACCOUNTS'])
    SPREADSHEET_KEY = os.environ['SPREADSHEET_KEY']
    secrets = get_secrets(role=getenv('VAULT_ROLE'))
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    #Initialize variables for getting google auth creds
    creds = Credentials.from_authorized_user_info(loads(secrets), scope)
    client_google = gspread.authorize(creds)
    list_checks=[]
    result_data=[]
    it=[]
    id=''
    #####
    #take one by one accounts from ACCOUNT variables
    for account_i in ACCOUNTS:
        sts_client = boto3.client('sts')
        assumed_role_object = sts_client.assume_role(
            RoleArn=account_i['role_arn'],
            RoleSessionName='AssumeRoleSession'
        )
        credentials = assumed_role_object['Credentials']
        client = boto3.client('support',aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'])
        response = client.describe_trusted_advisor_checks(language='en')
        list_checks = response['checks']
        for item in list_checks:
            if item['name'] == 'Unassociated Elastic IP Addresses':
                iditem = item['id']
        response_2=client.describe_trusted_advisor_check_result(checkId=iditem,language='en')
        #More about describe_trusted_advisor_check_result https://boto3.amazonaws.com/v1/documentation/api/1.26.87/reference/services/support/client/describe_trusted_advisor_check_result.html
        for instance in response_2['result']['flaggedResources']:
            it = instance['metadata']
            it.insert(0,account_i['name'])
            result_data.append(it)
        #print(result_data)
        #Send to GoogleSheets
        sheet = client_google.open_by_key(SPREADSHEET_KEY).worksheet('Elastic IPs')
        sheet.batch_clear(['A1:H1000'])
        sheet.append_row(["Account","Region","IP Address"], table_range="A1")
        sheet.freeze(rows=1, cols=1)
        sheet.format("A1:H1", {
            "backgroundColor": {
                "red": 0.79,
                "green": 0.85,
                "blue": 0.97
            },
              "textFormat": {"bold": True}
            })
        sheet.append_rows(result_data, table_range="A2")


