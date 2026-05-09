"""AWS account inventory via boto3.

Reads credentials from the standard chain (env vars, ~/.aws/credentials,
or IAM role). Never accepts secrets via HTTP.

Returns `{"connected": bool, ...}`. When connected, also returns
`account`, `arn`, `region`, `ec2`, `s3`.
"""
import os

from cache import ttl_cache


@ttl_cache(seconds=30.0)
def read() -> dict:
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
    except ImportError:
        return {"connected": False, "error": "boto3 not installed"}

    try:
        session = boto3.Session()
        if session.get_credentials() is None:
            return {
                "connected": False,
                "error": (
                    "No AWS credentials found. Set AWS_ACCESS_KEY_ID/"
                    "AWS_SECRET_ACCESS_KEY, run `aws configure`, or attach an IAM role."
                ),
            }

        region = session.region_name or os.environ.get("AWS_REGION", "us-east-1")
        identity = session.client("sts", region_name=region).get_caller_identity()

        result = {
            "connected": True,
            "account": identity["Account"],
            "arn": identity["Arn"],
            "region": region,
        }

        try:
            ec2 = session.client("ec2", region_name=region)
            states: dict = {}
            total = 0
            for page in ec2.get_paginator("describe_instances").paginate():
                for r in page["Reservations"]:
                    for i in r["Instances"]:
                        s = i["State"]["Name"]
                        states[s] = states.get(s, 0) + 1
                        total += 1
            result["ec2"] = {"total": total, "by_state": states}
        except (ClientError, BotoCoreError) as e:
            result["ec2"] = {"error": str(e)}

        try:
            buckets = session.client("s3").list_buckets().get("Buckets", [])
            result["s3"] = {"buckets": len(buckets)}
        except (ClientError, BotoCoreError) as e:
            result["s3"] = {"error": str(e)}

        return result
    except (NoCredentialsError, ClientError, BotoCoreError) as e:
        return {"connected": False, "error": str(e)}
