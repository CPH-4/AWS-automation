![Header](https://github.com/user-attachments/assets/a52af369-408a-489e-94dd-47efd6c621d8)
## Identifying and managing abandoned AWS Infrastructure

Cloud-native environments offer a cost-effective way to manage resources, but proper monitoring of deployed infrastructure is crucial. When resources are spread across multiple regions and accounts, identifying unused objects can be challenging, resulting in unnecessary costs and security risks. This solution centralizes the monitoring of abandoned infrastructure, such as in a Google Sheet or a simple text file in an S3 bucket, for easier tracking and management of unused resources.
## What is it?
These handy scripts help obtain unused infrastructure objects from multiple AWS accounts and regions and save them in one place

## How to use it?
Deploy the required roles, event triggers, and Lambda functions, along with tailored scripts to meet your specific requirements. Configure the storage location for the data and provide the necessary credentials for access (Google Sheet or an S3 bucket)

## In more detail
![DF341D2A-D9F9-4A57-B594-256B5295142C](https://github.com/user-attachments/assets/70edba7c-eb13-452f-a102-0b87d6386b36)

**There are two types of scripts: one that uses Trusted Advisor and one that does not**

Scripts utilizing Trusted Advisor provide more comprehensive outputs, including details such as Account, Region/AZ, Instance ID, Instance Name, Instance Type, Estimated Monthly Savings, CPU/Network usage over 14 days, CPU Utilization 14-Day Average, Network I/O 14-Day Average, and the Number of Days with Low Utilization (for EC2 instances, as an example). However, these scripts require an AWS Business or Enterprise Support plan.
On the other hand, scripts that do not use Trusted Advisor are compatible with basic plans, offering an alternative for users without advanced support subscriptions.

#### Roles
There are two types of roles <br>

***Main IAM Role*** - This role allows assuming roles from other accounts and is located in the account containing the Lambda function, labeled main-assume-role in the scheme <br>
***Role for Observed Account*** - This role has permission to gather data from the account in which it is assigned and also has a trust relationship with the main account, identified as either role-for-trust-advisor-1 or role-assumed-by-main-acc in the scheme <br>

Used resources:
- Trusted Advisor
- Lambda function
- Event Bridge
- IAM Roles
- S3 bucket


<details>
<summary>Click to view the examples</summary>

![D0ADCE08-591A-4FE3-A125-3ED295823311](https://github.com/user-attachments/assets/de147cee-b8b2-4135-9697-368475c4cdc4)
![E8F6FA0F-DDB8-45FE-B6B9-3D9C0D11999F](https://github.com/user-attachments/assets/293b7787-5785-48ae-a56e-ab2a1bb52c8b)
![D0ADCE08-591A-4FE3-A125-3ED295823311](https://github.com/user-attachments/assets/8738856a-60ee-4c5f-95e3-7edcf57c2c1e)

Raw txt in S3 bucket
```
ACCOUNT   REGION        IP
account_1 eu-central-1	XX.XXX.XX.XXX	
account_1 eu-central-1	X.XXX.XXX.XXX
account_2 eu-west-2    	X.XXX.XXX.XXX
account_2 eu-north-1   	X.XXX.XXX.XXX
account_2 eu-north-1   	X.XXX.XXX.XXX
```

</details>
