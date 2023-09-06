import json, os
import requests
from pprintpp import pprint as pp
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from urllib.parse import urlparse
import boto3

CWD = os.path.dirname(__file__)

from get_apigw_url import get_apigw_url
from utils import join, from_json, simple_json_request, download_url, fmt_json

def rel_join(suffix, mkdir=False):
    return join(CWD, suffix, mkdir=mkdir)

PATH_TO_PAYLOAD = rel_join("payload.json")
PATH_TO_OUTPUT = rel_join("outputs/output.json", mkdir=True)
CONTROL_BROKER_STACK_NAME='ControlBrokerV0x10x1'

url = get_apigw_url(CONTROL_BROKER_STACK_NAME)

payload = {
    "Context":{
        "EnvironmentEvaluation":"Prod"
    },
    "Input":from_json(PATH_TO_PAYLOAD)
}

auth = BotoAWSRequestsAuth(
    aws_host= urlparse(url).hostname,
    aws_region=boto3.session.Session().region_name,
    aws_service='execute-api'
)

status_code, r = simple_json_request(url, payload, auth)
pp(r)
presigned_url = r['Response']['ControlBrokerEvaluation']['Raw']['PresignedUrl']

download_url(presigned_url, PATH_TO_OUTPUT)

fmt_json(PATH_TO_OUTPUT, PATH_TO_OUTPUT)
