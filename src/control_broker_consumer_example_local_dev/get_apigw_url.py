import re
import boto3
from pprintpp import pprint as pp


# Get the API Gateway URL from the CloudFormation stack output
def get_apigw_url(stack_name):
    cf_client = boto3.client('cloudformation')
    response = cf_client.describe_stacks(StackName=stack_name)
    outputs = response['Stacks'][0]['Outputs']
    for output in outputs:
        output_key=output['OutputKey']
        if output_key.startswith('ControlBrokerApiCloudFormationHandlerUrl'):
            return output['OutputValue']
    raise Exception('OutputKey not found')