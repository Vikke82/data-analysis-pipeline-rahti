# CSC Allas S3 Credentials - Troubleshooting Guide

## 🚨 Current Issue
Your credentials are returning "InvalidAccessKeyId" error, which means:
- The access key is not valid for S3 access to CSC Allas
- You might be using OpenStack/application credentials instead of S3 credentials
- Both your access key and secret key are identical, which is unusual for S3

## 🔧 How to Get Correct S3 Credentials

### Method 1: CSC Customer Portal (my.csc.fi)

1. **Login**: Go to https://my.csc.fi
2. **Select Project**: Choose project `2015319`
3. **Navigate to Services**: Find "Allas" in your project services
4. **Generate S3 Credentials**:
   - Look for "S3 Access Keys" or "Generate S3 Credentials"
   - Click "Create new S3 credentials" or similar
   - You should get:
     - `AWS_ACCESS_KEY_ID` (typically 20 characters)
     - `AWS_SECRET_ACCESS_KEY` (typically 40+ characters)

### Method 2: Using CSC Supercomputer (Recommended)

If you have access to Puhti or Mahti:

```bash
# SSH to Puhti
ssh your_csc_username@puhti.csc.fi

# Load allas module
module load allas

# Configure for S3 access
allas-conf -m S3

# Follow the prompts to authenticate with your CSC account
# This will create ~/.aws/credentials with proper S3 keys
```

After running `allas-conf -m S3`, check the generated credentials:
```bash
cat ~/.aws/credentials
```

You should see something like:
```ini
[default]
aws_access_key_id = AKIA...  (20 character string)
aws_secret_access_key = ...  (40+ character string)
```

### Method 3: Web Interface S3 Configuration

1. Go to Puhti/Mahti web interface: https://puhti.csc.fi
2. Use "Cloud storage configuration" app
3. Configure S3 connection for your project
4. Export the generated credentials

## 🔍 What Valid S3 Credentials Look Like

```env
# CORRECT S3 credentials format:
ALLAS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE    # 20 chars, starts with AKIA
ALLAS_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY  # 40+ chars, different from access key

# INCORRECT (what you currently have):
ALLAS_ACCESS_KEY=95261495737e4a77873dca19f6aeb8ad  # Same as secret key
ALLAS_SECRET_KEY=95261495737e4a77873dca19f6aeb8ad  # Same as access key
```

## 🎯 Next Steps

1. **Get proper S3 credentials** using one of the methods above
2. **Update your .env file** with the new credentials:
   ```env
   ALLAS_ACCESS_KEY=your_new_access_key
   ALLAS_SECRET_KEY=your_new_secret_key
   DATA_BUCKET=your_bucket_name
   ```
3. **Test the connection** again with `python test_allas_connection.py`
4. **Build and run** the containers once the connection works

## 📞 Getting Help

If you still have issues:
1. Contact CSC Service Desk: servicedesk@csc.fi
2. Mention you need S3 credentials for Allas access
3. Reference your project number: 2015319
4. Ask specifically for S3 access keys (not OpenStack credentials)

## 🔗 Useful Links

- CSC Customer Portal: https://my.csc.fi
- Allas Documentation: https://docs.csc.fi/data/Allas/
- S3 Access Guide: https://docs.csc.fi/data/Allas/using_allas/python_boto3/
