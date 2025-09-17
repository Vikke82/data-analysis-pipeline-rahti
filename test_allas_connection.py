#!/usr/bin/env python3
"""
Test script to verify CSC Allas connection using boto3
Run this script to test your Allas S3 credentials before building the containers
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_allas_connection():
    """Test connection to CSC Allas using boto3."""
    
    print("🧪 Testing CSC Allas Connection with boto3...")
    print("=" * 50)
    
    # Load environment variables
    access_key = "95261495737e4a77873dca19f6aeb8ad"
    secret_key = "95261495737e4a77873dca19f6aeb8ad"
    bucket_name = "cloudservices"
    
    if not all([access_key, secret_key, bucket_name]):
        print("❌ Missing credentials. Please check your .env file.")
        return False
    
    print(f"📝 Access Key: {access_key[:8]}***")
    print(f"📝 Secret Key: {secret_key[:8]}***")
    print(f"📝 Bucket: {bucket_name}")
    print()
    
    try:
        # Set up environment variables for boto3
        os.environ["AWS_ACCESS_KEY_ID"] = access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
        os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "when_required"
        os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "when_required"
        
        # Create boto3 S3 client pointing to CSC Allas
        print("🔗 Connecting to CSC Allas at https://a3s.fi...")
        s3_client = boto3.client('s3', endpoint_url='https://a3s.fi')
        
        # First, try to list all available buckets
        print("🔍 Listing all available buckets...")
        try:
            buckets_response = s3_client.list_buckets()
            available_buckets = [bucket['Name'] for bucket in buckets_response.get('Buckets', [])]
            
            if available_buckets:
                print(f"✅ Found {len(available_buckets)} available buckets:")
                for bucket in available_buckets:
                    print(f"   📦 {bucket}")
                    
                # Check if the specified bucket exists
                if bucket_name in available_buckets:
                    print(f"✅ Target bucket '{bucket_name}' exists in your account")
                    target_bucket = bucket_name
                else:
                    print(f"⚠️  Target bucket '{bucket_name}' not found in your account")
                    print(f"🔄 Using first available bucket: '{available_buckets[0]}'")
                    target_bucket = available_buckets[0]
            else:
                print("❌ No buckets found in your account")
                return False
                
        except Exception as bucket_error:
            print(f"❌ Error listing buckets: {bucket_error}")
            return False
        
        # Test connection by checking bucket access
        print(f"🔍 Checking access to bucket '{target_bucket}'...")
        s3_client.head_bucket(Bucket=target_bucket)
        print("✅ Successfully connected to bucket!")
        
        # List some files
        print(f"📁 Listing files in bucket '{target_bucket}'...")
        response = s3_client.list_objects_v2(Bucket=target_bucket, MaxKeys=10)
        
        if 'Contents' in response:
            file_count = len(response['Contents'])
            print(f"✅ Found {file_count} files (showing first 10):")
            for obj in response['Contents']:
                size_mb = obj['Size'] / (1024 * 1024)
                print(f"   📄 {obj['Key']} ({size_mb:.2f} MB)")
        else:
            print("ℹ️  Bucket is empty or no files found")
            
        # Update .env file if we used a different bucket
        if target_bucket != bucket_name:
            print(f"")
            print(f"💡 Suggestion: Update your .env file to use bucket '{target_bucket}':")
            print(f"   DATA_BUCKET={target_bucket}")
        
        print()
        print("🎉 Connection test SUCCESSFUL!")
        print("🚀 You can now proceed with: docker-compose up -d")
        return True
        
    except NoCredentialsError:
        print("❌ AWS credentials not found or invalid")
        return False
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error'].get('Message', 'Unknown error')
        
        print(f"❌ AWS Client Error (Code: {error_code}): {error_message}")
        
        if error_code == '403':
            print("🔍 Troubleshooting Access Denied (403):")
            print("   1. Verify your S3 credentials are correct")
            print("   2. Check if the bucket name is correct")
            print("   3. Ensure your CSC project has Allas access enabled")
            print("   4. Try listing all buckets first to see what's available")
            print("")
            print("💡 To get correct S3 credentials:")
            print("   1. Go to https://my.csc.fi")
            print("   2. Select your project")
            print("   3. Click 'Allas' service")
            print("   4. Generate new S3 credentials (Access Key + Secret Key)")
            
        elif error_code == '404':
            print(f"❌ Bucket '{bucket_name}' does not exist")
            print("💡 Try creating the bucket first or use an existing one")
        elif error_code == 'InvalidAccessKeyId':
            print("❌ Invalid Access Key ID")
            print("💡 Check your ALLAS_ACCESS_KEY in .env file")
        elif error_code == 'SignatureDoesNotMatch':
            print("❌ Invalid Secret Key")
            print("💡 Check your ALLAS_SECRET_KEY in .env file")
        else:
            print(f"❌ Other AWS error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_allas_connection()
    sys.exit(0 if success else 1)
