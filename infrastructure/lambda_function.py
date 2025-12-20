import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Project Zeus: Serverless Health Monitor
    Triggered by CloudWatch Events to log system status.
    """
    logger.info("Zeus Monitor triggered.")
    
    # In a real scenario, this might check an endpoint or database
    health_status = {
        "status": "healthy",
        "service": "Zeus-Engine",
        "region": event.get("region", "unknown")
    }
    
    logger.info(f"Health Check Status: {json.dumps(health_status)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(health_status)
    }
