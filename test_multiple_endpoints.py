#!/usr/bin/env python3
"""
Test script to try different CSC Allas endpoints and credential formats
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_multiple_endpoints():
    """Test connection to CSC Allas using different endpoints."""
    
    access_key = "95261495737e4a77873dca19f6aeb8ad"
    secret_key = "95261495737e4a77873dca19f6aeb8ad"
    
    # Different endpoints to try
    endpoints = [
        "https://a3s.fi",
        "https://allas.csc.fi",
        "https://object.pouta.csc.fi"
    ]
    
    print("🧪 Testing multiple CSC Allas endpoints...")
    print("=" * 60)
    
    for endpoint in endpoints:
        print(f"\n🔗 Testing endpoint: {endpoint}")
        
        try:
            # Set environment variables
            os.environ["AWS_ACCESS_KEY_ID"] = access_key
            os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
            os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "when_required"
            os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "when_required"
            
            # Create S3 client
            s3_client = boto3.client('s3', endpoint_url=endpoint)
            
            # Try to list buckets
            response = s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
            
            print(f"✅ SUCCESS with {endpoint}")
            print(f"📦 Found {len(buckets)} buckets:")
            for bucket in buckets:
                print(f"   - {bucket}")
            return endpoint, buckets
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"❌ Failed with {endpoint}: {error_code}")
            
        except Exception as e:
            print(f"❌ Failed with {endpoint}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("❌ All endpoints failed!")
    print("\n💡 This strongly suggests invalid S3 credentials.")
    print("🔧 You need to generate proper S3 credentials:")
    print("   1. Go to https://my.csc.fi")
    print("   2. Select project 2015319")
    print("   3. Go to Allas service")
    print("   4. Generate S3 credentials (not application credentials)")
    print("   5. Look for 'AWS_ACCESS_KEY_ID' and 'AWS_SECRET_ACCESS_KEY'")
    
    return None, []

if __name__ == "__main__":
    endpoint, buckets = test_multiple_endpoints()
    
    if endpoint and buckets:
        print(f"\n🎉 Successful connection found!")
        print(f"📝 Update your docker-compose.yml to use: {endpoint}")
        print(f"📝 Available buckets: {', '.join(buckets)}")
    else:
        print(f"\n❌ No working connection found. Please get valid S3 credentials.")
