import os
import argparse
import boto3
from botocore.exceptions import ClientError

def parse_active_storage(env='development'):
    config = {}
    try:
        with open('active_storage.yml', 'r') as f:
            content = f.read()
            in_env = False
            for line in content.split('\n'):
                line = line.rstrip()
                if line == f"{env}:":
                    in_env = True
                    continue
                elif line and not line.startswith('  ') and in_env: # assuming indentation is 2 spaces
                    # wait, if line doesn't start with space, we might be out of env, but careful with empty lines
                    if line != "":
                        in_env = False
                
                if in_env and ':' in line:
                    key, val = line.split(':', 1)
                    config[key.strip()] = val.strip()
    except Exception as e:
        print(f"Could not read active_storage.yml: {e}")
    return config

def upload_file(file_name, bucket, access_key, secret_key, region, endpoint, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_name)

    # For boto3, endpoint should not have the bucket name in the host if we pass Bucket to the API.
    # DigitalOcean endpoint is like https://syd1.digitaloceanspaces.com
    # If the user put https://ai10x.syd1.digitaloceanspaces.com, we can strip the bucket prefix:
    if endpoint and f"{bucket}." in endpoint:
        endpoint = endpoint.replace(f"{bucket}.", "")

    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=region,
                            endpoint_url=endpoint,
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key)

    try:
        client.upload_file(file_name, bucket, object_name)
        print(f"Successfully uploaded {file_name} to Space '{bucket}' as '{object_name}'")
    except ClientError as e:
        print(f"Error uploading file: {e}")
        return False
    except Exception as e:
        print(f"Exception: {e}")
        return False
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Upload a file to DigitalOcean Spaces via CLI")
    parser.add_argument('file', help="Path to the file to upload")
    parser.add_argument('--env', default='development', help="Environment to read from active_storage.yml")
    parser.add_argument('--bucket', help="Name of the DigitalOcean Space (bucket). Overrides active_storage.yml")
    parser.add_argument('--object-name', help="Destination object name (defaults to file name)")
    args = parser.parse_args()

    config = parse_active_storage(args.env)
    
    bucket = args.bucket or config.get('bucket')
    access_key = os.environ.get('DO_ACCESS_KEY_ID') or config.get('access_key_id')
    secret_key = os.environ.get('DO_SECRET_ACCESS_KEY') or config.get('secret_access_key')
    region = os.environ.get('DO_REGION') or config.get('region', 'syd1')
    endpoint = os.environ.get('DO_ENDPOINT') or config.get('endpoint', 'https://syd1.digitaloceanspaces.com')

    if not all([bucket, access_key, secret_key, endpoint]):
        print("Missing required configuration (bucket, access_key, secret_key, endpoint).")
        exit(1)

    upload_file(args.file, bucket, access_key, secret_key, region, endpoint, args.object_name)
