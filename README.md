# CSC Allas Data Analysis Pipeline

A containerized data analysis pipeline designed for ingesting, processing, and visualizing data from CSC Allas object storage. This pipeline consists of three main services working together to provide a complete data analysis solution.

**🎓 Educational Project**: This repository is designed for students learning cloud services and data analysis. Fork it to create your own implementation!

## 📚 For Students: Getting Started

### Step 1: Fork This Repository

1. **Fork the repository:**
   - Go to: https://github.com/Vikke82/data-analysis-pipeline-rahti
   - Click the "Fork" button in the top right
   - Choose your GitHub account to fork to
   - This creates your own copy that you can modify

2. **Clone your fork locally:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/data-analysis-pipeline-rahti.git
   cd data-analysis-pipeline-rahti
   ```

3. **Set up your development environment:**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your CSC credentials (see configuration section below)
   notepad .env  # Windows
   nano .env     # Linux/Mac
   ```

### Step 2: Configure Your CSC Credentials

Edit the `.env` file with your CSC Allas credentials:

```env
# CSC Allas Configuration
OS_AUTH_URL=https://pouta.csc.fi:5001/v3
OS_USERNAME=your_csc_username
OS_PASSWORD=your_csc_password
OS_PROJECT_NAME=project_XXXXXXX
OS_PROJECT_DOMAIN_NAME=Default
OS_USER_DOMAIN_NAME=Default
DATA_BUCKET=your_container_name
```

**Where to get these credentials:**
1. **CSC Username/Password**: Your CSC account credentials
2. **Project Name**: Found in CSC My CSC portal (format: project_XXXXXXX)
3. **Data Bucket**: Name of your Allas container (you can create one in CSC portal)

### Step 3: Test Locally (Optional)

```bash
# Build and run locally with Docker
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f

# Access the dashboard
# Open browser to: http://localhost:8501

# Stop services
docker-compose down
```

### Step 4: Deploy to CSC Rahti

#### Prerequisites:
- CSC account with Rahti access
- OpenShift CLI (`oc`) installed
- Your fork of the repository

#### Deployment Steps:

1. **Login to CSC Rahti:**
   ```bash
   oc login https://api.2.rahti.csc.fi:6443
   ```

2. **Create your project:**
   ```bash
   # Replace YOUR_NUMBER with your CSC project number
   # Replace YOUR_PROJECT_NAME with a unique name
   oc new-project YOUR_PROJECT_NAME --description="csc_project: YOUR_NUMBER"
   ```

3. **Create credentials secret:**
   ```bash
   oc create secret generic allas-credentials \
     --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 \
     --from-literal=OS_USERNAME=your_csc_username \
     --from-literal=OS_PASSWORD=your_csc_password \
     --from-literal=OS_PROJECT_NAME=project_XXXXXXX \
     --from-literal=OS_PROJECT_DOMAIN_NAME=Default \
     --from-literal=OS_USER_DOMAIN_NAME=Default \
     --from-literal=DATA_BUCKET=your_container_name
   ```

4. **Deploy services directly from GitHub (Recommended Method):**

   This method bypasses registry issues by using OpenShift's source-to-image capability:

   ```bash
   # Deploy data-ingest service
   oc new-app https://github.com/YOUR_USERNAME/data-analysis-pipeline-rahti.git --context-dir=data-ingest --name=data-ingest
   
   # Deploy data-clean service
   oc new-app https://github.com/YOUR_USERNAME/data-analysis-pipeline-rahti.git --context-dir=data-clean --name=data-clean
   
   # Deploy data-visualization service
   oc new-app https://github.com/YOUR_USERNAME/data-analysis-pipeline-rahti.git --context-dir=data-visualization --name=data-visualization
   
   # Deploy Redis service
   oc new-app redis:7-alpine --name=redis
   ```

5. **Set up environment variables for all services:**
   ```bash
   # Link Allas credentials to all services
   oc set env deployment/data-ingest --from=secret/allas-credentials
   oc set env deployment/data-clean --from=secret/allas-credentials
   oc set env deployment/data-visualization --from=secret/allas-credentials
   ```

6. **Configure resource limits to avoid quota issues:**

   **⚠️ Important**: CSC projects have CPU and memory quotas. Set appropriate limits:

   ```bash
   # Set resource limits for Redis (lightweight)
   oc set resources deployment redis --limits=cpu=100m,memory=256Mi --requests=cpu=50m,memory=128Mi
   
   # Set resource limits for data-ingest
   oc set resources deployment data-ingest --limits=cpu=200m,memory=512Mi --requests=cpu=100m,memory=256Mi
   
   # Set resource limits for data-clean
   oc set resources deployment data-clean --limits=cpu=300m,memory=768Mi --requests=cpu=150m,memory=384Mi
   
   # Set resource limits for data-visualization
   oc set resources deployment data-visualization --limits=cpu=300m,memory=768Mi --requests=cpu=150m,memory=384Mi
   ```

   **Resource Planning Guide:**
   - **Total CPU needed**: ~900m (0.9 cores)
   - **Total Memory needed**: ~2.3GB
   - **Recommended project quota**: At least 1 CPU core and 3GB memory

7. **Expose the web interface:**
   ```bash
   # Create external route for the dashboard
   oc expose service/data-visualization
   ```

8. **Verify deployment:**
   ```bash
   # Check pods status (all should be Running)
   oc get pods
   
   # Get your application URL
   oc get routes
   
   # Check resource usage against quota
   oc describe quota
   
   # View logs if needed
   oc logs -f deployment/data-visualization
   ```

### Step 5: Customize Your Implementation

**🎯 Assignment Ideas for Students:**

1. **Data Source Modification:**
   - Add your own dataset to Allas
   - Modify the ingestion service for different file formats
   - Implement custom data validation rules

2. **Analysis Enhancement:**
   - Add new data cleaning operations
   - Implement additional quality metrics
   - Create custom visualization components

3. **Infrastructure Improvements:**
   - Add monitoring and alerting
   - Implement automated scaling
   - Add backup and recovery mechanisms

4. **Security Enhancements:**
   - Implement application credentials
   - Add HTTPS encryption
   - Set up proper access controls

### Step 6: Submit Your Work

**For Course Submission:**
1. **Document your changes** in your fork's README
2. **Create a demo video** showing your pipeline working
3. **Include screenshots** of your Rahti deployment
4. **Write a report** about challenges and solutions
5. **Share your repository URL** with instructors

**Repository Structure for Students:**
```
your-fork/
├── README.md                 # Your documentation
├── docs/                     # Additional documentation
│   ├── DEPLOYMENT_LOG.md     # Your deployment experience
│   ├── CUSTOMIZATIONS.md     # Changes you made
│   └── SCREENSHOTS/          # Deployment screenshots
├── data-ingest/             # Ingestion service (customize here)
├── data-clean/              # Cleaning service (customize here)
├── data-visualization/      # Streamlit dashboard (customize here)
├── k8s/                     # Kubernetes manifests
└── .env.example             # Template for credentials
```

## 🚀 Advanced: Automated Deployment with GitHub Actions

For advanced students who want to implement CI/CD:

### Step 1: Set Up GitHub Secrets

In your forked repository, go to **Settings > Secrets and variables > Actions** and add:

```
RAHTI_SERVER=https://api.2.rahti.csc.fi:6443
RAHTI_TOKEN=your_openshift_token
RAHTI_PROJECT=your-project-name
CSC_PROJECT_NUMBER=your_csc_project_number
OS_USERNAME=your_csc_username
OS_PASSWORD=your_csc_password
OS_PROJECT_NAME=project_XXXXXXX
DATA_BUCKET=your_container_name
```

**How to get OpenShift token:**
```bash
oc login https://api.2.rahti.csc.fi:6443
oc whoami -t
```

### Step 2: Create GitHub Actions Workflow

Create `.github/workflows/deploy-to-rahti.yml`:

```yaml
name: Deploy to CSC Rahti

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup OpenShift CLI
      uses: redhat-actions/openshift-tools-installer@v1
      with:
        oc: 4
    
    - name: Login to OpenShift
      run: |
        oc login --token="${{ secrets.RAHTI_TOKEN }}" --server="${{ secrets.RAHTI_SERVER }}"
        oc project ${{ secrets.RAHTI_PROJECT }} || oc new-project ${{ secrets.RAHTI_PROJECT }} --description="csc_project: ${{ secrets.CSC_PROJECT_NUMBER }}"
    
    - name: Create/Update Secrets
      run: |
        oc delete secret allas-credentials --ignore-not-found
        oc create secret generic allas-credentials \
          --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 \
          --from-literal=OS_USERNAME="${{ secrets.OS_USERNAME }}" \
          --from-literal=OS_PASSWORD="${{ secrets.OS_PASSWORD }}" \
          --from-literal=OS_PROJECT_NAME="${{ secrets.OS_PROJECT_NAME }}" \
          --from-literal=OS_PROJECT_DOMAIN_NAME=Default \
          --from-literal=OS_USER_DOMAIN_NAME=Default \
          --from-literal=DATA_BUCKET="${{ secrets.DATA_BUCKET }}"
    
    - name: Deploy to OpenShift
      run: |
        # Apply Kubernetes manifests
        oc apply -f k8s/
        
        # Wait for deployment
        oc rollout status deployment/data-ingest
        oc rollout status deployment/data-clean
        oc rollout status deployment/data-visualization
        oc rollout status deployment/redis
        
        # Get application URL
        echo "Application URL:"
        oc get routes data-visualization -o jsonpath='{.spec.host}'
```

### Step 3: Enable Automated Deployments

1. **Commit the workflow:**
   ```bash
   git add .github/workflows/deploy-to-rahti.yml
   git commit -m "Add automated deployment to Rahti"
   git push origin main
   ```

2. **Watch the deployment:**
   - Go to your repository's **Actions** tab
   - Watch the deployment progress
   - Check logs if there are any issues

3. **Verify deployment:**
   ```bash
   # Check your OpenShift project
   oc get pods
   oc get routes
   ```

This setup enables **automatic deployment** every time you push changes to your main branch!

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Ingest   │───▶│   Data Clean    │───▶│ Data Visualization │
│  (CSC Allas)    │    │  (Processing)   │    │   (Streamlit)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │     Redis       │
                    │ (Coordination)  │
                    └─────────────────┘
```

### Services Overview

- **🔄 Data Ingest Service**: Connects to CSC Allas and downloads data files on a scheduled basis
- **🧹 Data Clean Service**: Processes, cleans, and validates the ingested data
- **📊 Data Visualization Service**: Provides a Streamlit dashboard for data exploration and monitoring
- **🔗 Redis**: Coordinates between services and tracks processing status

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- CSC Allas account with API credentials
- At least 2GB available RAM
- Port 8501 available for the web interface

### Setup Instructions

1. **Clone and navigate to the project directory:**
   ```powershell
   cd "Data analysis pipeline container"
   ```

2. **Configure environment variables:**
   ```powershell
   Copy-Item .env.example .env
   ```
   
   Edit `.env` file with your CSC Allas S3 credentials:
   ```env
   ALLAS_ACCESS_KEY=your_s3_access_key_here
   ALLAS_SECRET_KEY=your_s3_secret_key_here
   DATA_BUCKET=your_bucket_name
   ```

3. **Start the pipeline:**
   ```powershell
   docker-compose up -d
   ```

4. **Access the dashboard:**
   Open your web browser and go to: `http://localhost:8501`

5. **Monitor logs (optional):**
   ```powershell
   docker-compose logs -f
   ```

## 📋 Detailed Setup

### CSC Allas Configuration

1. **Get your S3 credentials from CSC Allas:**
   - Log into [CSC Customer Portal](https://my.csc.fi)
   - Navigate to your project
   - Go to "Allas" service
   - Generate S3 credentials (Access Key and Secret Key)

2. **Prepare your data bucket:**
   - Create a bucket in Allas (or use existing one)
   - Upload your data files (CSV, JSON, Excel, or text files)
   - Note the bucket name for configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLAS_ACCESS_KEY` | Allas S3 access key | Required |
| `ALLAS_SECRET_KEY` | Allas S3 secret key | Required |
| `DATA_BUCKET` | Name of your data bucket | Required |

## 🔧 Service Details

### Data Ingest Service

**Purpose**: Automatically downloads and processes data from CSC Allas using the S3/boto3 protocol

**Features**:
- Uses recommended boto3 library for S3 protocol access
- Supports multiple file formats (CSV, JSON, Excel, TXT)
- Incremental sync (only downloads new/changed files)
- Automatic file format detection
- Error handling and retry logic
- Status tracking via Redis
- Direct connection to CSC Allas at https://a3s.fi

**Configuration**:
- Runs every 15 minutes by default
- Maximum file size: 100MB
- Supports custom delimiters for text files

**Supported File Formats**:
- **CSV**: Standard comma-separated values
- **JSON**: Single objects or arrays of objects
- **Excel**: .xlsx and .xls files
- **Text**: Tab, semicolon, or pipe-delimited files

### Data Clean Service

**Purpose**: Processes and cleans the ingested data

**Features**:
- **Data Quality Assessment**: Comprehensive quality scoring
- **Duplicate Removal**: Identifies and removes duplicate records
- **Missing Value Handling**: Smart imputation based on column types
- **Data Type Standardization**: Automatic type detection and conversion
- **Outlier Detection**: Statistical outlier identification and handling
- **Column Name Cleaning**: Standardizes column names
- **Quality Reporting**: Detailed quality metrics and recommendations

**Quality Metrics**:
- **Completeness**: Percentage of non-null values
- **Uniqueness**: Percentage of unique records
- **Consistency**: Data format consistency
- **Validity**: Percentage of valid values

**Processing Pipeline**:
1. Load raw data
2. Remove duplicates
3. Clean column names
4. Handle missing values
5. Standardize data types
6. Detect and handle outliers
7. Generate quality report
8. Save cleaned data

### Data Visualization Service

**Purpose**: Provides interactive dashboards for data exploration

**Features**:
- **Pipeline Monitoring**: Real-time status of all services
- **Data Quality Dashboard**: Visual quality metrics and recommendations
- **Interactive Visualizations**: Multiple chart types and filters
- **Data Explorer**: Column-by-column data profiling
- **Export Functionality**: Download processed data

**Available Visualizations**:
- Correlation heatmaps
- Distribution plots (histograms, box plots)
- Scatter plots with trend lines
- Time series analysis
- Bar charts and pie charts
- Violin plots for distribution analysis

**Dashboard Sections**:
1. **Pipeline Status**: Service health and last run times
2. **Data Overview**: Key metrics and data freshness
3. **Quality Assessment**: Detailed quality scores
4. **Statistical Summary**: Descriptive statistics
5. **Visualizations**: Interactive charts
6. **Data Explorer**: Column profiling
7. **Raw Data**: Filtered data viewing and export

## 🐳 Docker Configuration

### Build and Run

```powershell
# Build all services
docker-compose build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down

# Remove volumes (clean start)
docker-compose down -v
```

### Service Dependencies

The services start in the following order:
1. Redis (message broker and status storage)
2. Data Ingest (begins downloading data)
3. Data Clean (waits for ingested data)
4. Data Visualization (provides web interface)

### Volume Management

- **shared-data**: Stores processed data files accessible by all services
- **redis-data**: Persistent storage for Redis status and coordination data

## 🌐 CSC Rahti Deployment

This pipeline can be deployed to CSC Rahti (OpenShift) for production use. All deployment files and scripts are provided.

### Prerequisites for Rahti Deployment

- CSC account with Rahti access enabled
- OpenShift CLI (`oc`) installed
- Your CSC project number for billing/quota
- Docker for building images

### Step-by-Step Rahti Deployment

#### 1. Login to CSC Rahti
```powershell
# Login with correct Rahti URL
oc login https://api.2.rahti.csc.fi:6443

# Create project (replace YOUR_NUMBER with your CSC project number)
oc new-project your-data-pipeline --description="csc_project: YOUR_NUMBER"
```

#### 2. Create Kubernetes Secret for Allas Credentials

Your `.env` file already contains the Allas credentials. Create a Kubernetes secret from these:

```powershell
# Create secret using your existing .env credentials
oc create secret generic allas-credentials \
  --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 \
  --from-literal=OS_USERNAME=villemaj \
  --from-literal=OS_PASSWORD=M3r1h3lm1D4n13l \
  --from-literal=OS_PROJECT_NAME=project_2015319 \
  --from-literal=OS_PROJECT_DOMAIN_NAME=Default \
  --from-literal=OS_USER_DOMAIN_NAME=Default \
  --from-literal=DATA_BUCKET=cloudservices
```

**Where are credentials stored?**
- **Location**: Inside your OpenShift project on CSC Rahti
- **Type**: Kubernetes Secret object (encrypted)
- **Name**: `allas-credentials`
- **Access**: Only pods in your project can use these credentials
- **Security**: No local files created - everything stored securely in the cluster

**Verify the secret was created:**
```powershell
# List all secrets in your project
oc get secrets

# View secret details (values are base64 encoded for security)
oc describe secret allas-credentials
```

#### 3. Build and Push Docker Images

Use the provided automation script:
```powershell
# Build and push all container images
.\build-and-push.ps1
```

This script will:
- Build all Docker images locally
- Tag them for the chosen registry
- Push them to CSC Rahti's integrated registry (recommended)

#### 4. Deploy the Pipeline

Deploy all services to Rahti:
```powershell
# Deploy complete pipeline to CSC Rahti
.\deploy-to-rahti.ps1
```

This deploys:
- Data ingest service
- Data cleaning service  
- Data visualization service (Streamlit dashboard)
- Redis coordination service
- Persistent storage for processed data
- External route for web access

#### 5. Verify Deployment

```powershell
# Check all pods are running
oc get pods

# Check services
oc get services

# Get external URL for your dashboard
oc get routes

# View logs if needed
oc logs -f deployment/data-visualization
```

### Credential Management Options

For production security, consider using **Application Credentials** instead of your main CSC password:

1. **Create Application Credentials:**
   - Go to https://pouta.csc.fi
   - Navigate to Identity > Application Credentials
   - Create new credential named "data-pipeline-rahti"
   - Copy the ID and Secret

2. **Use Application Credentials:**
   ```powershell
   # Delete existing secret
   oc delete secret allas-credentials
   
   # Create new secret with application credentials
   oc create secret generic allas-credentials \
     --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 \
     --from-literal=OS_APPLICATION_CREDENTIAL_ID=your_app_cred_id \
     --from-literal=OS_APPLICATION_CREDENTIAL_SECRET=your_app_cred_secret \
     --from-literal=DATA_BUCKET=cloudservices
   ```

### Advanced Credential Management

Use the interactive credential management tool:
```powershell
.\manage-allas-credentials.ps1
```

This tool provides options to:
- Create new credentials
- Update existing credentials
- View current credentials (masked)
- Delete credentials
- Set up application credentials
- Test Allas connection

### Scaling and Monitoring

```powershell
# Scale services based on load
oc scale deployment data-clean --replicas=2

# Monitor resource usage
oc top pods

# Update deployment with new image
oc set image deployment/data-ingest data-ingest=new-image:tag

# Rollback if needed
oc rollout undo deployment/data-ingest
```

## 🔧 Student Troubleshooting Guide

### Common Issues and Solutions for Students

#### 1. "Permission denied" when creating OpenShift project

**Problem:** Error when running `oc new-project`
```
Error from server: admission webhook "project.admission.webhook" denied the request
```

**Solution:** Make sure you include your CSC project number in the description:
```bash
oc new-project your-project-name --description="csc_project: YOUR_NUMBER"
```

#### 2. CSC Credentials not working

**Problem:** Authentication failures with Allas

**Solutions:**
```bash
# 1. Test your credentials locally first
python test_allas_connection.py

# 2. Verify credentials in CSC portal
# Go to: https://my.csc.fi

# 3. Check project name format (should be: project_XXXXXXX)
echo $OS_PROJECT_NAME

# 4. Try application credentials instead of password
# (See CSC Pouta dashboard > Application Credentials)
```

#### 3. "Image pull errors" in Rahti

**Problem:** Pods can't pull Docker images

**Solutions:**
```bash
# 1. Use Rahti's integrated registry (recommended for students)
oc policy add-role-to-user registry-viewer developer
oc policy add-role-to-user registry-editor developer

# 2. Check image names in deployment files
oc describe pod <pod-name>

# 3. Rebuild and push images
./build-and-push.ps1
```

#### 4. "No raw files to process" message

**Problem:** Data clean service can't find files

**Solutions:**
```bash
# 1. Check if ingestion service is working
oc logs -f deployment/data-ingest

# 2. Verify Allas container has data
# Login to CSC portal and check your Allas container

# 3. Check shared volume permissions
oc exec -it deployment/data-ingest -- ls -la /shared/data
```

#### 5. Streamlit dashboard not loading

**Problem:** Can't access the web interface

**Solutions:**
```bash
# 1. Check if route exists
oc get routes

# 2. Check service status
oc get services

# 3. Check pod logs
oc logs -f deployment/data-visualization

# 4. Port forward for testing
oc port-forward service/data-visualization 8501:8501
# Then access: http://localhost:8501
```

#### 6. "Insufficient quota" errors

**Problem:** Not enough resources in your project

**Solutions:**
```bash
# 1. Check current resource usage
oc describe quota

# 2. Reduce resource requests in deployment files
# Edit k8s/*-deployment.yaml files
# Lower memory/CPU requests

# 3. Contact CSC support if you need more quota
```

#### 7. GitHub Actions deployment failing

**Problem:** Automated deployment not working

**Solutions:**
1. **Check secrets are set correctly** in GitHub Settings > Secrets
2. **Verify token is still valid:**
   ```bash
   oc login --token=YOUR_TOKEN --server=https://api.2.rahti.csc.fi:6443
   oc whoami
   ```
3. **Check workflow logs** in GitHub Actions tab
4. **Test deployment manually first** before automating

#### 9. Quota and Resource Management Issues

**Problem:** "exceeded quota" errors when deploying

**Solutions:**
```bash
# 1. Check your current quota usage
oc describe quota

# 2. View resource consumption by pods
oc top pods

# 3. Reduce resource limits if needed
oc set resources deployment DEPLOYMENT_NAME --limits=cpu=200m,memory=512Mi --requests=cpu=100m,memory=256Mi

# 4. Scale down deployments temporarily
oc scale deployment DEPLOYMENT_NAME --replicas=0

# 5. Check CSC project quota limits in CSC portal
# Go to: https://my.csc.fi
```

**Recommended Resource Allocation:**
- **Redis**: CPU: 100m, Memory: 256Mi
- **Data-ingest**: CPU: 200m, Memory: 512Mi  
- **Data-clean**: CPU: 300m, Memory: 768Mi
- **Data-visualization**: CPU: 300m, Memory: 768Mi
- **Total**: ~900m CPU, ~2.3GB Memory

#### 10. Build and Deployment Failures

**Problem:** Services fail to build or deploy

**Solutions:**
```bash
# 1. Check build logs
oc logs -f buildconfig/SERVICE_NAME

# 2. Check deployment events
oc get events --sort-by='.lastTimestamp' | tail -20

# 3. Restart failed builds
oc start-build SERVICE_NAME

# 4. Delete and redeploy problematic services
oc delete deployment SERVICE_NAME
oc new-app https://github.com/YOUR_USERNAME/data-analysis-pipeline-rahti.git --context-dir=SERVICE_FOLDER --name=SERVICE_NAME
```

### 📞 Getting Help

1. **Check service logs first:**
   ```bash
   oc logs -f deployment/SERVICE_NAME
   ```

2. **Use the CSC documentation:**
   - [CSC Allas Guide](https://docs.csc.fi/data/Allas/)
   - [CSC Rahti Guide](https://docs.csc.fi/cloud/rahti/)

3. **Contact CSC Service Desk:**
   - Email: servicedesk@csc.fi
   - Include your project number and error messages

4. **Ask your instructor or teaching assistants**

5. **Check the repository issues:**
   - Go to: https://github.com/Vikke82/data-analysis-pipeline-rahti/issues

### 🔍 Debugging Guide for Students

#### Step-by-Step Debugging Process

**1. Check Overall Status:**
```bash
# Get overview of all resources
oc status

# Check pod health
oc get pods -o wide

# Check deployments
oc get deployments

# Check services
oc get services

# Check routes
oc get routes
```

**2. Identify Problem Pods:**
```bash
# Look for pods with status: CrashLoopBackOff, Error, ImagePullBackOff
oc get pods

# Get detailed pod information
oc describe pod POD_NAME

# Check pod logs (current and previous)
oc logs POD_NAME
oc logs POD_NAME --previous
```

**3. Debug Resource Issues:**
```bash
# Check quota usage
oc describe quota

# Check node resource availability
oc describe nodes

# Check resource consumption
oc top pods
oc top nodes
```

**4. Debug Networking Issues:**
```bash
# Check if services are properly exposed
oc get endpoints

# Test service connectivity from within cluster
oc run debug-pod --image=busybox --rm -it --restart=Never -- nslookup redis

# Test external route
curl -I http://YOUR-ROUTE-URL
```

**5. Debug Environment Variables:**
```bash
# Check if secrets exist
oc get secrets

# Verify secret content (keys only, values are base64 encoded)
oc describe secret allas-credentials

# Check if environment variables are set in deployments
oc set env deployment/SERVICE_NAME --list

# Test environment variables in running pod
oc exec -it deployment/SERVICE_NAME -- env | grep OS_
```

**6. Debug Build Issues:**
```bash
# Check build configs
oc get buildconfigs

# Check build status
oc get builds

# View build logs
oc logs -f build/BUILD_NAME

# Trigger new build
oc start-build BUILDCONFIG_NAME
```

#### Common Debug Commands Cheat Sheet

```bash
# Quick health check of all services
oc get pods,svc,routes

# Follow logs from all services
oc logs -f deployment/data-ingest &
oc logs -f deployment/data-clean &
oc logs -f deployment/data-visualization &
oc logs -f deployment/redis &

# Check recent events (shows last 20 events)
oc get events --sort-by='.lastTimestamp' | tail -20

# Port forward for local testing
oc port-forward service/data-visualization 8501:8501
# Then access: http://localhost:8501

# Execute commands inside containers
oc exec -it deployment/SERVICE_NAME -- /bin/bash
oc exec -it deployment/SERVICE_NAME -- env
oc exec -it deployment/SERVICE_NAME -- ls -la /shared/data

# Scale services up/down
oc scale deployment SERVICE_NAME --replicas=0  # Stop
oc scale deployment SERVICE_NAME --replicas=1  # Start

# Restart deployment (force pod recreation)
oc rollout restart deployment/SERVICE_NAME

# Check deployment history and rollback if needed
oc rollout history deployment/SERVICE_NAME
oc rollout undo deployment/SERVICE_NAME
```

#### Debugging Specific Issues

**Application Shows "Not Available" Page:**
1. Check pod status: `oc get pods`
2. Check if pods are running: `oc logs -f deployment/data-visualization`
3. Verify route exists: `oc get routes`
4. Test port forwarding: `oc port-forward service/data-visualization 8501:8501`

**Data Not Processing:**
1. Check Allas credentials: `oc set env deployment/data-ingest --list`
2. Verify bucket access: `oc logs -f deployment/data-ingest`
3. Check Redis connectivity: `oc exec -it deployment/redis -- redis-cli ping`
4. Monitor data flow: `oc exec -it deployment/data-clean -- ls -la /shared/data`

**Services Crashing:**
1. Check resource limits: `oc describe deployment SERVICE_NAME`
2. Review crash logs: `oc logs POD_NAME --previous`
3. Check quota usage: `oc describe quota`
4. Verify environment variables: `oc set env deployment/SERVICE_NAME --list`

**Build Failures:**
1. Check Dockerfile syntax in GitHub repository
2. Verify build logs: `oc logs -f buildconfig/SERVICE_NAME`
3. Check source code changes: Compare with working version
4. Retry build: `oc start-build SERVICE_NAME`

### 📊 Monitoring and Maintenance

#### Resource Monitoring Commands
```bash
# Monitor resource usage over time
watch -n 5 'oc top pods'

# Check detailed resource consumption
oc describe node NODE_NAME | grep -A 5 "Allocated resources"

# Monitor quota usage
watch -n 10 'oc describe quota'

# View resource requests and limits
oc get pods -o custom-columns=NAME:.metadata.name,CPU_REQ:.spec.containers[*].resources.requests.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,CPU_LIM:.spec.containers[*].resources.limits.cpu,MEM_LIM:.spec.containers[*].resources.limits.memory
```

#### Application Health Monitoring
```bash
# Set up health check endpoints monitoring
curl -f http://YOUR-ROUTE/health || echo "Service down"

# Monitor application metrics (if available)
curl http://YOUR-ROUTE/metrics

# Monitor log patterns for errors
oc logs -f deployment/SERVICE_NAME | grep -i error

# Check application response times
time curl -s http://YOUR-ROUTE > /dev/null
```

#### Automated Monitoring Script
Create a monitoring script that you can run periodically:

```bash
#!/bin/bash
# save as monitor.sh

echo "=== Pod Status ==="
oc get pods

echo "=== Resource Usage ==="
oc top pods 2>/dev/null || echo "Metrics not available"

echo "=== Quota Usage ==="
oc describe quota | grep -A 10 "Resource\|Used"

echo "=== Recent Events ==="
oc get events --sort-by='.lastTimestamp' | tail -10

echo "=== Service Endpoints ==="
curl -I http://YOUR-ROUTE 2>/dev/null | head -1 || echo "Service not responding"
```

Run with: `bash monitor.sh`

#### Maintenance Tasks

**Regular Cleanup:**
```bash
# Clean up old builds (keep last 3)
oc get builds --sort-by='.metadata.creationTimestamp' | head -n -3 | awk '{print $1}' | xargs oc delete build

# Clean up failed pods
oc delete pods --field-selector=status.phase=Failed

# Clean up completed jobs (if any)
oc delete jobs --field-selector=status.successful=1
```

**Backup Important Data:**
```bash
# Export configurations
oc export all > backup-configs.yaml
oc export secrets > backup-secrets.yaml

# Backup application data (if stored in volumes)
oc exec -it deployment/SERVICE_NAME -- tar -czf /tmp/backup.tar.gz /shared/data
oc cp POD_NAME:/tmp/backup.tar.gz ./data-backup.tar.gz
```

**Performance Optimization:**
```bash
# Adjust resource limits based on actual usage
oc patch deployment SERVICE_NAME -p '{"spec":{"template":{"spec":{"containers":[{"name":"SERVICE_NAME","resources":{"limits":{"cpu":"NEW_LIMIT","memory":"NEW_LIMIT"}}}]}}}}'

# Scale services based on load
oc scale deployment SERVICE_NAME --replicas=2  # Scale up
oc scale deployment SERVICE_NAME --replicas=1  # Scale down
```

### 💡 Pro Tips for Students

1. **Always test locally first** before deploying to Rahti
2. **Use small datasets** for initial testing
3. **Keep credentials secure** - never commit them to Git
4. **Document your deployment process** for your report
5. **Take screenshots** of working deployment for submission
6. **Monitor resource usage** to avoid quota issues

### Troubleshooting Rahti Deployment

**Pod not starting:**
```powershell
oc describe pod <pod-name>
oc logs <pod-name>
```

**Credential issues:**
```powershell
# Test credentials with the management script
.\manage-allas-credentials.ps1
# Choose option 6 (Test connection)
```

**Route not accessible:**
```powershell
oc get routes
oc describe service data-visualization
```

**Data not processing:**
```powershell
# Check data-ingest logs
oc logs -f deployment/data-ingest

# Verify Redis connectivity
oc exec -it deployment/redis -- redis-cli ping
```

### Security Best Practices for Rahti

- ✅ Use application credentials (not main password)
- ✅ Regularly rotate credentials
- ✅ Monitor access logs in CSC portal
- ✅ Set appropriate resource limits
- ✅ Review external route security settings
- ✅ Use separate credentials per environment

### Rahti Deployment Files

All necessary Kubernetes manifests and scripts are provided:

- `k8s/` - Kubernetes deployment manifests
- `RAHTI_DEPLOYMENT_GUIDE.md` - Detailed deployment guide
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
- `deploy-to-rahti.ps1` - Automated deployment script
- `build-and-push.ps1` - Image build automation
- `manage-allas-credentials.ps1` - Credential management tool

## 📊 Monitoring and Troubleshooting

### Health Checks

Each service includes health monitoring:

```powershell
# Check service status
docker-compose ps

# View specific service logs
docker-compose logs data-ingest
docker-compose logs data-clean
docker-compose logs data-visualization
```

### Common Issues

1. **No data in dashboard**:
   - Check if Allas credentials are correct
   - Verify bucket name and data files exist
   - Check data-ingest service logs

2. **Pipeline stuck**:
   - Restart services: `docker-compose restart`
   - Check Redis connectivity
   - Review error logs

3. **Quality issues**:
   - Review quality report recommendations
   - Check data source formatting
   - Adjust quality thresholds in configuration

4. **Performance issues**:
   - Monitor resource usage: `docker stats`
   - Consider increasing processing intervals
   - Check file sizes and formats

### Log Locations

Logs are accessible via Docker Compose:
```powershell
# All services
docker-compose logs

# Specific service
docker-compose logs [service-name]

# Follow logs in real-time
docker-compose logs -f
```

## 🔒 Security Considerations

1. **Environment Variables**: Store sensitive data in `.env` file, never in code
2. **Network**: Services communicate on isolated Docker network
3. **Data Access**: Shared volumes are accessible only to authorized containers
4. **API Keys**: Rotate CSC Allas credentials regularly

## 📈 Performance Tuning

### Resource Allocation

Default resource limits are set conservatively. For better performance:

1. **Increase memory limits** in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
   ```

2. **Adjust processing schedules**:
   - Reduce ingestion frequency for large datasets
   - Increase cleaning interval if processing is slow

3. **Optimize data formats**:
   - Use CSV for best performance
   - Avoid very wide datasets (>100 columns)

### Scaling Considerations

- **Horizontal**: Run multiple pipeline instances with different buckets
- **Vertical**: Increase container resources
- **Storage**: Use external storage for large datasets

## 🛠️ Development

### Adding New Data Sources

1. Extend `allas_client.py` with new connection methods
2. Update `data_processor.py` for new formats
3. Add configuration options to pipeline.json

### Custom Visualizations

1. Add new chart methods to `visualizations.py`
2. Update `app.py` to include new visualization options
3. Test with sample data

### Quality Metrics

1. Extend `quality_checker.py` with new assessment methods
2. Update thresholds in configuration
3. Add corresponding dashboard components

## 📚 API Reference

### Redis Keys

| Key Pattern | Description |
|-------------|-------------|
| `sync_status` | Overall ingestion status |
| `cleaning_status` | Overall cleaning status |
| `file:{filename}` | Individual file timestamps |
| `status:{filename}` | Individual file processing status |
| `clean_status:{filename}` | Individual file cleaning status |

### Data File Naming

| Pattern | Description |
|---------|-------------|
| `raw_{filename}` | Ingested raw data |
| `cleaned_{filename}` | Processed clean data |
| `summary_{filename}.json` | Quality assessment report |

## 📄 License

This project is intended for use with CSC Allas and follows CSC's terms of service.

## 🤝 Support

For technical support:
1. Check the troubleshooting section above
2. Review service logs for error messages
3. Verify CSC Allas connectivity and credentials
4. Ensure Docker resources are sufficient

## 📋 Changelog

### Version 1.0.0
- Initial release with full pipeline functionality
- CSC Allas integration
- Comprehensive data cleaning
- Interactive Streamlit dashboard
- Docker containerization
- Redis-based coordination
