#!/usr/bin/env python3
"""
Test script for CSC Allas Swift connection
Based on CSC documentation: https://docs.csc.fi/data/Allas/using_allas/rclone_local/
"""
import os
import sys
from pathlib import Path
import logging

# Add the data-ingest directory to the path to import the client
current_dir = Path(__file__).parent
data_ingest_dir = current_dir / "data-ingest"
sys.path.append(str(data_ingest_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_env_file():
    """Load environment variables from .env file"""
    env_file = current_dir / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
                    except ValueError:
                        continue

def test_swift_connection():
    """Test the Swift connection to CSC Allas"""
    print("=" * 60)
    print("CSC ALLAS SWIFT CONNECTION TEST")
    print("=" * 60)
    
    # Load environment variables
    load_env_file()
    
    # Check required environment variables
    required_vars = [
        'OS_AUTH_URL',
        'OS_USERNAME', 
        'OS_PASSWORD',
        'OS_PROJECT_NAME'
    ]
    
    print("Checking environment variables...")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: NOT SET")
        else:
            if var == 'OS_PASSWORD':
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
    
    print(f"✅ OS_PROJECT_DOMAIN_NAME: {os.getenv('OS_PROJECT_DOMAIN_NAME', 'Default')}")
    print(f"✅ OS_USER_DOMAIN_NAME: {os.getenv('OS_USER_DOMAIN_NAME', 'Default')}")
    print(f"✅ DATA_BUCKET: {os.getenv('DATA_BUCKET', 'data-container')}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\n🔧 To fix this:")
        print("1. Set the missing variables in your .env file")
        print("2. Get credentials from Puhti:")
        print("   module load allas")
        print("   allas-conf --show-powershell")
        print("3. Or use CSC's web interface: https://my.csc.fi")
        return False
    
    print("\n" + "=" * 60)
    print("TESTING SWIFT CONNECTION")
    print("=" * 60)
    
    try:
        # Import and test the Allas client
        from allas_client import AllasClient
        
        print("Creating Allas client...")
        with AllasClient() as client:
            print("✅ Client created successfully!")
            
            print("\nListing containers...")
            containers = client.list_containers()
            print(f"✅ Found {len(containers)} containers:")
            for container in containers[:5]:  # Show first 5
                print(f"  - {container}")
            if len(containers) > 5:
                print(f"  ... and {len(containers) - 5} more")
            
            print(f"\nTesting default container: {client.container_name}")
            try:
                files = client.list_files()
                print(f"✅ Found {len(files)} files in container '{client.container_name}':")
                for file_info in files[:3]:  # Show first 3
                    print(f"  - {file_info['name']} ({file_info['size']} bytes)")
                if len(files) > 3:
                    print(f"  ... and {len(files) - 3} more files")
            except Exception as e:
                print(f"⚠️  Container '{client.container_name}' might be empty or not exist: {e}")
            
            print("\nGetting container info...")
            try:
                bucket_info = client.get_bucket_info()
                print(f"✅ Container info:")
                print(f"  - Name: {bucket_info['bucket_name']}")
                print(f"  - Objects: {bucket_info['object_count']}")
                print(f"  - Total size: {bucket_info['total_size_mb']} MB")
            except Exception as e:
                print(f"⚠️  Could not get container info: {e}")
            
            print("\n🎉 Swift connection test completed successfully!")
            return True
            
    except ImportError as e:
        print(f"❌ Failed to import required modules: {e}")
        print("Make sure python-swiftclient and python-keystoneclient are installed:")
        print("pip install python-swiftclient python-keystoneclient")
        return False
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Verify your CSC credentials are correct")
        print("2. Make sure your project has Allas access enabled") 
        print("3. Check if you need to renew your authentication token")
        print("4. Try connecting from Puhti first to verify credentials")
        return False

if __name__ == "__main__":
    success = test_swift_connection()
    sys.exit(0 if success else 1)
