import json
import re

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

class SimpleControlBrokerClient():
    
    def __init__(self,*,
        invoke_url,
        input_bucket,
        input_object:dict,
    ):
        
        self.invoke_url = invoke_url
        self.input_bucket = input_bucket
        self.input_object = input_object
        
        self.put_input()
        self.invoke_endpoint()
    
        
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
        
        print(f'\napigw formatted response:\n{r}')
        
        return r


with open('invoke-url.json','r') as f:
    invoke_url = json.loads(f.read())

print(f'invoke_url:\n{invoke_url}\n')

input_analyzed_path = './input_analyzed/ControlBrokerEvalEngineExampleAppStackSQS.template.json'

with open(input_analyzed_path,'r') as f:
    input_analyzed:dict = json.loads(f.read())


input_bucket = 'cschneider-control-broker-utils'

input_analyzed = {
    'Bucket': input_bucket,
    'Key': input_analyzed_path.split('/')[-1]
}

put_object(
    bucket = input_analyzed['Bucket'],
    key = input_analyzed['Key'],
    object_ = input_analyzed
)



cb_input_object = {
    "ConsumerMetadata":{
        "foo":"Bar"
    },
    "InputAnalyzed": input_analyzed
}


s = SimpleControlBrokerClient(
    invoke_url = invoke_url,
    input_bucket = input_bucket,
    input_object = cb_input_object
)