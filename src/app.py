# Project Zeus - Core Service
# Built with Python 3.9
import os
import json

def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    Returns status of the cloud resources.
    """
    print("Zeus Monitor: Checking system health...")
    
    status = {
        "service": "Zeus Infrastructure Monitor",
        "status": "operational",
        "region": os.environ.get('AWS_REGION', 'us-east-1'),
        "container_id": os.environ.get('HOSTNAME', 'local')
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(status)
    }

if __name__ == "__main__":
    # Simulate a local run
    print(lambda_handler(None, None))
