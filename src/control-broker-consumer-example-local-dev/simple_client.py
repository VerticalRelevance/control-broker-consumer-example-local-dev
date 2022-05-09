import json
import re
from time import sleep

import requests
from pprintpp import pprint as pp
import boto3
from botocore.exceptions import ClientError
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

s3 = boto3.client('s3')

session = boto3.session.Session()
region = session.region_name
account_id = boto3.client('sts').get_caller_identity().get('Account')


def put_object(*,bucket,key,object_:dict):
    
    print(f'begin put_object\nbucket:\n{bucket}\nkey:\n{key}')
    
    try:
        r = s3.put_object(
            Bucket = bucket,
            Key = key,
            Body = json.dumps(object_)
        )
    except ClientError as e:
        print(f'ClientError:\nbucket:\n{bucket}\nkey:\n{key}\n{e}')
        raise
    else:
        print(f'no ClientError put_object:\nbucket:\n{bucket}\nkey:\n{key}')
        return True

def get_object(*,bucket,key):
    
    try:
        r = s3.get_object(
            Bucket = bucket,
            Key = key
        )
    except ClientError as e:
        print(e)
        if e.response['ResponseMetadata']['HTTPStatusCode'] == 403:
            print(f'403 as proxy for nonexistance, but may hide actual actual IAM issues')
            return False
        if e.response['ResponseMetadata']['HTTPStatusCode'] == 404:
            return False
        else:
            raise
    else:
        print(f'no ClientError get_object:\nbucket:\n{bucket}\nkey:\n{key}')
        body = r['Body']
        content = json.loads(body.read().decode('utf-8'))
        return content

def retry_get_object(*,bucket,key):
    
    for i in range(4):
        content = get_object(bucket=bucket,key=key)
        try:
            assert content
        except AssertionError:
            print('sleep')
            sleep(i**2)
        else:
            return content
    else:
        print('failed')
        
class SimpleControlBrokerClient():
    
    def __init__(self,*,
        invoke_url,
        input_bucket,
        input_object:dict,
    ):
        
        self.invoke_url = invoke_url
        self.input_bucket = input_bucket
        self.input_object = input_object
        
        
    def put_input(self):
        
        put = put_object(
            bucket=self.input_bucket,
            key='SimpleControlBrokerClient-input.json',
            object_ = self.input_object
        )
        
    def invoke_endpoint(self):
        
        def get_host(*,full_invoke_url):
            m = re.search('https://(.*)/.*',full_invoke_url)
            return m.group(1)
        
        host = get_host(full_invoke_url=self.invoke_url)
            
        auth = BotoAWSRequestsAuth(
            aws_host= host,
            aws_region=region,
            aws_service='execute-api'
        )
        
        r = requests.post(
            self.invoke_url,
            auth = auth,
            json = self.input_object
        )
        
        print(f'headers:\n{dict(r.request.headers)}\n')
        
        content = json.loads(r.content)
        
        r = {
            'StatusCode':r.status_code,
            'Content': content
        }
        
        print(f'\napigw formatted response:\n')
        pp(r)
        
        return r

with open('invoke-url.json','r') as f:
    invoke_url = json.loads(f.read())

print(f'invoke_url:\n{invoke_url}\n')

# input_analyzed_path = './input_analyzed/ControlBrokerEvalEngineExampleAppStackSQS.template.json'
input_analyzed_path = './input_analyzed/ConfigEvent.sqs.queue.json'

with open(input_analyzed_path,'r') as f:
    input_analyzed_object:dict = json.loads(f.read())

input_bucket = 'cschneider-control-broker-utils' # edit bucket policy to allow CB.Reader.RoleArn

input_analyzed = {
    'Bucket': input_bucket,
    'Key': input_analyzed_path.split('/')[-1]
}

put_object(
    bucket = input_analyzed['Bucket'],
    key = input_analyzed['Key'],
    object_ = input_analyzed_object
)

cb_input_object = {
    "Context":{
        "EnvironmentEvaluation":"Prod"
    },
    "Input": input_analyzed
}

s = SimpleControlBrokerClient(
    invoke_url = invoke_url,
    input_bucket = input_bucket,
    input_object = cb_input_object
)

s.put_input()
response = s.invoke_endpoint()

raw_bucket = response['Content']['Response']['ResultsReport']['Buckets']['Raw']

output_handlers = response['Content']['Response']['ResultsReport']['Buckets']['OutputHandlers']

result = retry_get_object(
    # bucket = raw_bucket,
    bucket = [i['AccessPointArn'] for i in output_handlers if i['HandlerName'] == "CloudFormationOPA"][0],
    key = response['Content']['Response']['ResultsReport']['Key'],
)

pp(result)