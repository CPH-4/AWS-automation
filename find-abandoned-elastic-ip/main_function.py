#==============================================================
# 1.Initialize the environment variable ACCOUNT to consist of a list of account Names with their associated role ARNs in format [{'name':'ACC_NAME', 'role_arn': 'ROLEARN}]
# 2.Create a role with the following permissions: ec2:DescribeAddresses, ec2:DescribeRegions for monitored accounts, along with a role that Lambda can assume to access them
# 3.Add Lambda Layer with requred dependencies or add its by archive https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
# Set up place where you will push your data and set up required credentals / Google Sheets in this example
#==============================================================

import boto3
from json import dumps
from json import loads
from httplib2 import Http
from datetime import datetime, timedelta
import hvac
import os
from os import getenv
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.credentials import Credentials

def lambda_handler(event, context):
    # TODO implement
    req=get_checks()
    return {
        'statusCode': 200,
        'body': 'ok'
    }
    
def get_secrets(role):
#=========================
#
#Get the credentials or tokens for the place where you are going to publish the obtained results
#In that case, Vault was used
#
#=========================
    return secrets['data']['data']['token']
    
##################################
def get_checks():
    ACCOUNTS = eval(os.environ['ACCOUNTS'])
    unattached_eips =[] 
    main_txt = []

    for account_i in ACCOUNTS:
        sts_client = boto3.client('sts', region_name='eu-west-1', endpoint_url='https://sts.eu-west-1.amazonaws.com')
        assumed_role_object = sts_client.assume_role(RoleArn=account_i['role_arn'], RoleSessionName='AssumeRoleSession')
        credentials = assumed_role_object['Credentials']
        client = boto3.client('ec2',aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'])
        regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
        for reg in regions:
                client = boto3.client('ec2', aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],region_name=reg)
                #Get eip 
                response = client.describe_addresses()
                unattached_eips = [[account_i["name"],reg, eip["PublicIp"]]
                for eip in response.get("Addresses", [])
                if eip.get("AssociationId") is None]
                if unattached_eips:
                    main_txt.append(unattached_eips)
    send_action(main_txt[0])

def send_action(main_txt):
    #Data for google autrh creds
    SPREADSHEET_KEY = getenv("SPREADSHEET_KEY")
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    secrets = get_secrets(role=getenv('VAULT_ROLE'))
    creds = Credentials.from_authorized_user_info(loads(secrets), scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet('Elastic IPs')
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
    sheet.append_rows(main_txt, table_range="A2")
