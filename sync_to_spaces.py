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
                elif line and not line.startswith('  ') and in_env:
                    if line != "":
                        in_env = False
                
                if in_env and ':' in line:
                    key, val = line.split(':', 1)
                    config[key.strip()] = val.strip()
    except Exception as e:
        print(f"Could not read active_storage.yml: {e}")
    return config

def sync_directory(directory, bucket, access_key, secret_key, region, endpoint):
    if endpoint and f"{bucket}." in endpoint:
        endpoint = endpoint.replace(f"{bucket}.", "")

    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=region,
                            endpoint_url=endpoint,
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key)

    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            object_name = os.path.relpath(file_path, directory)
            try:
                print(f"Uploading {file_path} to {bucket}/{object_name}...")
                client.upload_file(file_path, bucket, object_name)
            except ClientError as e:
                print(f"Error uploading {file_path}: {e}")
            except Exception as e:
                print(f"Exception: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sync a directory to DigitalOcean Spaces")
    parser.add_argument('--directory', default='tmp/storage', help="Directory to sync")
    parser.add_argument('--env', default='development', help="Environment to read from active_storage.yml")
    args = parser.parse_args()

    # Make sure we're in the right directory to find active_storage.yml
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    config = parse_active_storage(args.env)
    
    bucket = config.get('bucket')
    access_key = os.environ.get('DO_ACCESS_KEY_ID') or config.get('access_key_id')
    secret_key = os.environ.get('DO_SECRET_ACCESS_KEY') or config.get('secret_access_key')
    region = os.environ.get('DO_REGION') or config.get('region', 'syd1')
    endpoint = os.environ.get('DO_ENDPOINT') or config.get('endpoint', 'https://syd1.digitaloceanspaces.com')

    if not all([bucket, access_key, secret_key, endpoint]):
        print("Missing required configuration.")
        exit(1)

    sync_directory(args.directory, bucket, access_key, secret_key, region, endpoint)
