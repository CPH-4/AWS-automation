#==============================================================
# 1.Initialize the environment variable ACCOUNT to consist of a list of account Names with their associated role ARNs in format [{'name':'ACC_NAME', 'role_arn': 'ROLEARN}]
# 2.Create a role with the following permissions: ec2:DescribeVolumes, ec2:DescribeRegions, and s3:PutObject for monitored accounts, along with a role that Lambda can assume to access them
# 3.Add Lambda Layer with requred dependencies or add its by archive https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
# 4.Create an S3 bucket with required directory to store the collected data
#==============================================================


import boto3
import os
from httplib2 import Http

def lambda_handler(event, context):
    # TODO implement
    req=get_checks()
    return {
        'statusCode': 200,
        'body': 'ok'
    }

def get_checks():
    ACCOUNTS = eval(os.environ['ACCOUNTS'])
    main_txt = ''
    current_txt = ''
    for account in ACCOUNTS:
                # sts_client will get credentials for each listed account https://docs.aws.amazon.com/STS/latest/APIReference/welcome.html
                sts_client = boto3.client('sts', region_name='eu-west-1', endpoint_url='https://sts.eu-west-1.amazonaws.com')
                assumed_role_object = sts_client.assume_role(
                    RoleArn=account['role_arn'],
                    RoleSessionName='AssumeRoleSession'
                )
                credentials = assumed_role_object['Credentials']
                client = boto3.client('ec2', aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'])
                #Get list of available regions
                regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
                for reg in regions:
                    client = boto3.client('ec2', aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'],region_name=reg)
                    #Get all unattached EBS in region
                    response = client.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
                    if response:
                        for item in list(response.items())[0][1]:
                            order = [account["name"],reg,item["VolumeId"],item["Size"]]
                            current_txt = ", ".join(str(order_item) for order_item in order) + '\n'
                            main_txt += current_txt

    write_to_s3(main_txt)
#Push to S3 bucket            
def write_to_s3(stanza):
    encoded_string = stanza.encode("utf-8")
    bucket_name = "list-abandoned-ebs-volumes"
    file_name = "ebs_list.txt"
    s3_path = "/" + file_name
    s3 = boto3.resource("s3")
    s3.Bucket(bucket_name).put_object(Key=s3_path, Body=encoded_string)

