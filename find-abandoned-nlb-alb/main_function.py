# To execute this script, it is necessary to specify the environments
# 1. List of account and Rols ACCOUNTS = [{'name':'account_1', 'role_arn': 'arn:aws:iam::111111111111:role/role-assumed-by-main-acc'}, {'name':'account_2', 'role_arn': 'arn:aws:iam::222222222222:role/role-assumed-by-main-acc'}]
# where key - "name" consist name of observed account
# "role_arn" key: The ARN of the role in that account that has permissions to perform actions for gathering data from the observed account. 
# Role from main account must have permission to assume this Role
# 2. Credentials for accessing Google Sheets
# 3. WORKSHEETS_NAME = {'elb': 'NLB ans ALB'} - reflect tab name in tables
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
    VAULT_ROLE = getenv("VAULT_ROLE") 
    ACCOUNTS = eval(os.environ['ACCOUNTS'])
    resp_acc=acc_cred(ACCOUNTS)
    # Set up Google Sheets authentication
    total_res = []
    #global result_elb_list
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

#Get credentials 
def acc_cred(acclist):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    secrets = get_secrets(role=getenv('VAULT_ROLE'))
    #Initialize variables for getting google auth creds
    creds = Credentials.from_authorized_user_info(loads(secrets), scope)
    client = gspread.authorize(creds)
    SPREADSHEET_KEY = getenv("SPREADSHEET_KEY")
    result_elb_list_acc = []
    total_res = []
    #take one by one accounts from ACCOUNT variables
    for account in acclist:
        sts_client = boto3.client('sts')
        assumed_role_object = sts_client.assume_role(
            RoleArn=account['role_arn'],
            RoleSessionName='AssumeRoleSession'
        )
        credentials = assumed_role_object['Credentials']
        ec2_client = boto3.client('ec2', aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'])
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
        #take one by one regions
        for reg in regions:
            elbv2_client = boto3.client('elbv2', aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'])
            load_balancer_response = elbv2_client.describe_load_balancers()
            load_balancer_arns = [lb['LoadBalancerArn'] for lb in load_balancer_response['LoadBalancers']]
            current_elb_metrics = get_elb_list(reg,load_balancer_arns,credentials)
            if current_elb_metrics:
                result_elb_list_acc.extend(current_elb_metrics)
    #Send to GoogleSheets
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet('Load balancers')
    sheet.batch_clear(['A1:H1000'])
    sheet.append_row(["ELB Name", "Region", "Account"], table_range="A1")
    sheet.freeze(rows=1, cols=1)
    sheet.format("A1:H1", {
    "backgroundColor": {
    "red": 0.79,
    "green": 0.85,
    "blue": 0.97
    },
    "textFormat": {"bold": True}
    })
    sheet.append_rows(result_elb_list_acc, table_range="A2")

    
#################################################
# Getitng  Network/Application load balancers withot new connections during 24h 
#################################################
#More about function get_metric_data https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch/client/get_metric_data.html
def get_elb_list(region,list_arns,creda):
    #get metrics from cloudwatch for each region
    counter=0
    result_elb_list_per_reg = [] 
    final_res=""
    client_cw = boto3.client('cloudwatch', aws_access_key_id=creda['AccessKeyId'],
        aws_secret_access_key=creda['SecretAccessKey'],
        aws_session_token=creda['SessionToken'])
    for arn in list_arns:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=14)
        name_elb = re.findall("app/.*|net/.*",arn)[0]
        if (name_elb[:3]) == 'app':
            metric_response = client_cw.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'm1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/ApplicationELB',
                            'MetricName': 'NewConnectionCount',
                            'Dimensions': [
                                {
                                    'Name': 'LoadBalancer',
                                    'Value': name_elb
                                }
                            ]
                        },
                        'Period': 86400,
                        'Stat': 'Sum'
                    },
                    'ReturnData': True
                }
            ],
            StartTime=start_time,
            EndTime=end_time
            )
        elif (name_elb[:3]) == 'net':
            metric_response = client_cw.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'm1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/NetworkELB',
                            'MetricName': 'ActiveFlowCount',
                            'Dimensions': [
                                {
                                    'Name': 'LoadBalancer',
                                    'Value': name_elb
                                }
                            ]
                        },
                        'Period': 86400,
                        'Stat': 'Sum'
                    },
                    'ReturnData': True
                }
            ],
            StartTime=start_time,
            EndTime=end_time
            )
        region=re.split(":",arn)[3]
        account=re.split(":",arn)[4]
        if not metric_response['MetricDataResults'][0]['Values']:
           result_elb_list_per_reg.append([str(name_elb),str(region), account])
    return result_elb_list_per_reg

