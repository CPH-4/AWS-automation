#==============================================================
# 1.Initialize the environment variable ACCOUNT to consist of a list of account Names with their associated role ARNs in format [{'name':'ACC_NAME', 'role_arn': 'ROLEARN}]
# 2.Create a role with the following permissions: support:describe_trusted_advisor_checks, support:describe_trusted_advisor_check_resul for monitored accounts, along with a role that Lambda can assume to access them
# 3.Add Lambda Layer with requred dependencies or add its by archive https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
# Set up place where you will push your data and set up required credentals / Google Sheets in this example
#==============================================================

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
#You can use more convenient way for store secrets for Google auth process
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
    #Variables for getting google auth creds
    VAULT_ROLE = getenv("VAULT_ROLE_LNK")
    #Variables for getting accounts and push to google table
    ACCOUNTS = eval(os.environ['ACCOUNTS'])
    SPREADSHEET_KEY = os.environ['SPREADSHEET_KEY']
    secrets = get_secrets(role=getenv('VAULT_ROLE'))
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    #Set up the client to work with Google Tables
    #More about usage authorization process: https://docs.gspread.org/en/latest/oauth2.html
    creds = Credentials.from_authorized_user_info(loads(secrets), scope)
    client_google = gspread.authorize(creds)
    list_checks=[]
    result_data=[]
    it=[]
    id=''
    ####################################
    #take one by one accounts from ACCOUNT variables
    for account_i in ACCOUNTS:
    #Get credental data for access to AWS api by boto3.client
    #More about usage boto3.client you can find here https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials
        sts_client = boto3.client('sts')
        assumed_role_object = sts_client.assume_role(
            RoleArn=account_i['role_arn'],
            RoleSessionName='AssumeRoleSession'
        )
        credentials = assumed_role_object['Credentials']
        client = boto3.client('support',aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'])
   #Call describe_trusted_advisor_checks https://boto3.amazonaws.com/v1/documentation/api/1.26.93/reference/services/support/client/describe_trusted_advisor_checks.html#describe-trusted-advisor-checks:~:text=describe_trusted_advisor_checks-,%C2%B6,-Support.Client.
        response = client.describe_trusted_advisor_checks(language='en')
        list_checks = response['checks']
        for item in list_checks:
            if item['name'] == 'Low Utilization Amazon EC2 Instances':
                iditem = item['id']
   #Call describe_trusted_advisor_check_result for exact check_id gained by request above
   #More about funtion describe_trusted_advisor_check_result https://boto3.amazonaws.com/v1/documentation/api/1.26.87/reference/services/support/client/describe_trusted_advisor_check_result.html
        response_2=client.describe_trusted_advisor_check_result(checkId=iditem,language='en')
        for instance in response_2['result']['flaggedResources']:
            it = instance['metadata']
            #Place the aws account name field in the first position on the list
            it.insert(0,account_i['name'])
   #Add string object to the list result_data initated before
   #This is done in order to send all collected data to Google Sheets by one api call
            result_data.append(it)
        #Get credential for Google sheets
        sheet = client_google.open_by_key(SPREADSHEET_KEY).worksheet('EC2 list')
        sheet.batch_clear(['A1:H1000'])
        sheet.append_row(["Account","Region/AZ", "Instance ID", "Instance Name", "Instance Type", "Estimated Monthly Savings", "CPU/Network Day 1","CPU/Network Day 2","CPU/Network Day 3","CPU/Network Day 4","CPU/Network Day 5","CPU/Network Day 6","CPU/Network Day 7","CPU/Network Day 8","CPU/Network Day 9","CPU/Network Day 10","CPU/Network Day 11","CPU/Network Day 12","CPU/Network Day 13","CPU/Network Day 14","CPU Utilization 14-Day Average", "Network I/O 14-Day Average", "Number of Days Low Utilization"], table_range="A1")
        sheet.freeze(rows=1, cols=1)
        sheet.format("A1:H1", {
            "backgroundColor": {
                "red": 0.79,
                "green": 0.85,
                "blue": 0.97
            },
              "textFormat": {"bold": True}
            })
        #Push data to the table by one call
        sheet.append_rows(result_data, table_range="A2")
