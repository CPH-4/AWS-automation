## Harvesting Abandoned AWS Infrastructure

Cloud-native environments offer an economical and effective solution for managing resources and infrastructure. However, it is crucial to properly monitor all deployed infrastructure. When resources are distributed across multiple regions and accounts, identifying and removing unused objects can become a significant challenge for administrators. Failing to delete certain types of unused resources in AWS can result in excessive costs, an increased threat landscape, and more complex operational activities.
This solution aims to centralize the monitoring of abandoned infrastructure of specific types, consolidating it in one place for easier management
For example, in Google Sheet.


**Two types of scripts are presented here: those that work with the Trusted Advisor service and those that do not**

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


<details>
<summary>Click to view the image</summary>






</details>
