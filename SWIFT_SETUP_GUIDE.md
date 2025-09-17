# CSC Allas Swift Authentication Setup Guide

This guide explains how to set up Swift authentication for CSC Allas using the OpenStack protocol, as recommended in the [CSC documentation](https://docs.csc.fi/data/Allas/using_allas/rclone_local/).

## Overview

We've switched from S3/boto3 to Swift/OpenStack protocol for better compatibility with CSC Allas. This approach is more stable and follows CSC's recommended practices.

## Required Environment Variables

The following environment variables need to be set in your `.env` file:

```bash
# OpenStack Swift Authentication for CSC Allas
OS_AUTH_URL=https://pouta.csc.fi:5001/v3
OS_USERNAME=your-csc-username
OS_PASSWORD=your-csc-password
OS_PROJECT_NAME=your-project-name
OS_PROJECT_DOMAIN_NAME=Default
OS_USER_DOMAIN_NAME=Default
DATA_BUCKET=cloudservices
```

## Getting Your Credentials

### Method 1: Using Puhti/Mahti (Recommended)

If you have access to CSC's supercomputers:

1. Connect to Puhti or Mahti
2. Load the Allas module:
   ```bash
   module load allas
   ```
3. Get your Swift credentials:
   ```bash
   allas-conf --show-powershell
   ```
4. Copy the PowerShell environment variable lines (starting with `$Env:`) and convert them:
   - `$Env:OS_AUTH_URL` → `OS_AUTH_URL`
   - `$Env:OS_USERNAME` → `OS_USERNAME` 
   - `$Env:OS_PASSWORD` → `OS_PASSWORD`
   - `$Env:OS_PROJECT_NAME` → `OS_PROJECT_NAME`

### Method 2: Using CSC Web Interface

1. Go to [https://my.csc.fi](https://my.csc.fi)
2. Log in with your CSC account
3. Navigate to your project
4. Go to Allas section
5. Look for OpenStack/Swift credentials (not S3)

### Method 3: Manual Setup

If you know your CSC credentials:

- `OS_USERNAME`: Your CSC username
- `OS_PASSWORD`: Your CSC password  
- `OS_PROJECT_NAME`: Your CSC project name (e.g., `project_2001234`)
- `OS_AUTH_URL`: Always `https://pouta.csc.fi:5001/v3`
- Domain names are usually `Default`

## Testing the Connection

After setting up your credentials:

1. Update the `.env` file with your actual credentials
2. Run the test script:
   ```bash
   python test_swift_connection.py
   ```

## Key Changes from S3 to Swift

- **Library**: Changed from `boto3` to `python-swiftclient` + `python-keystoneclient`
- **Authentication**: OpenStack Keystone v3 instead of S3 access keys
- **Endpoint**: Uses OpenStack API endpoint instead of S3 endpoint
- **Container**: Swift uses "containers" instead of "buckets"
- **Credentials**: Environment variables start with `OS_` instead of `ALLAS_`

## Docker Deployment

The Docker Compose configuration has been updated to pass the new environment variables:

```yaml
environment:
  - OS_AUTH_URL=${OS_AUTH_URL}
  - OS_USERNAME=${OS_USERNAME}
  - OS_PASSWORD=${OS_PASSWORD}
  - OS_PROJECT_NAME=${OS_PROJECT_NAME}
  - OS_PROJECT_DOMAIN_NAME=${OS_PROJECT_DOMAIN_NAME}
  - OS_USER_DOMAIN_NAME=${OS_USER_DOMAIN_NAME}
  - DATA_BUCKET=${DATA_BUCKET}
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**: 
   - Verify credentials are correct
   - Check if your authentication token has expired (Swift tokens expire after 8 hours)
   - Try authenticating on Puhti first to verify credentials

2. **Container Not Found**:
   - The container will be created automatically if it doesn't exist
   - Check that your project has Allas access enabled

3. **Import Errors**:
   - Make sure required packages are installed:
     ```bash
     pip install python-swiftclient python-keystoneclient
     ```

### Running the Pipeline

Once credentials are set up:

```bash
# Test connection
python test_swift_connection.py

# Build and run the pipeline
docker-compose up -d

# Check logs
docker-compose logs data-ingest
```

## Security Notes

- Swift credentials are more secure than S3 as they use token-based authentication
- Tokens expire automatically (typically after 8 hours)
- Always use environment variables, never hardcode credentials
- Consider using application credentials for production deployments

## Comparison: S3 vs Swift

| Aspect | S3 (Previous) | Swift (Current) |
|--------|---------------|-----------------|
| Protocol | S3 Compatible | OpenStack Swift |
| Library | boto3 | python-swiftclient |
| Auth | Access/Secret Keys | Username/Password + Token |
| Security | Static keys | Expiring tokens |
| CSC Recommendation | Supported | Preferred |
| Token Expiry | None | 8 hours |
| Container Creation | Manual | Automatic |

The Swift approach provides better security and follows CSC's recommended practices for Allas integration.
