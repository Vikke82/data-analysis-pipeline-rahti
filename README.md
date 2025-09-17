# CSC Allas Data Analysis Pipeline

A comprehensive containerized data analysis pipeline designed for ingesting, processing, and visualizing data from CSC Allas object storage. This pipeline runs as a **multi-container pod** on OpenShift/Kubernetes with shared volume architecture for seamless data flow between services.

**🎓 Educational Project**: This repository is designed for students learning cloud services, containerization, and data analysis pipelines. Fork it to create your own implementation!

## 🏗️ Architecture Overview

The pipeline consists of **four services running in a single pod** with shared storage:

### **📦 Multi-Container Pod Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    Data Pipeline Pod                         │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Redis Server  │  Data Ingestion │    Data Cleaning        │
│   localhost:6379│     Service     │      Service            │
├─────────────────┴─────────────────┴─────────────────────────┤
│              Data Visualization Service                     │
│                 (Streamlit Web App)                         │
├─────────────────────────────────────────────────────────────┤
│              Shared Volume: /shared/data                    │
│   • raw_data.csv        • cleaned_data.csv                  │
│   • summary_report.json • quality_metrics.json             │
└─────────────────────────────────────────────────────────────┘
```

### **🔄 Data Flow**
1. **Data Ingestion** → Downloads from CSC Allas → Saves to `/shared/data/raw_*.csv`
2. **Data Cleaning** → Reads raw files → Applies quality checks → Saves `cleaned_*.csv`
3. **Visualization** → Reads cleaned data → Displays interactive dashboard
4. **Redis Coordination** → Tracks processing status and inter-service communication

### **🎯 Key Benefits of This Architecture**
- ✅ **Shared Storage**: All containers access the same `/shared/data` directory
- ✅ **Fast Communication**: Localhost networking between services
- ✅ **Resource Efficiency**: Single pod deployment with optimized resource usage
- ✅ **Simplified Deployment**: One deployment instead of multiple separate services
- ✅ **Atomic Scaling**: All services scale together as a unit

## � Technical Specifications

### **Container Images & Technologies**
- **Base**: Python 3.11-slim (Debian-based)
- **Redis**: redis:7-alpine (lightweight coordination)
- **Web Framework**: Streamlit (interactive dashboards)
- **Data Processing**: pandas, numpy, matplotlib, plotly
- **Cloud Integration**: python-swiftclient, python-keystoneclient
- **Orchestration**: OpenShift/Kubernetes compatible

### **Resource Requirements**
| Resource | Minimum | Recommended | 
|----------|---------|-------------|
| **CPU** | 0.9 cores | 1.5 cores |
| **Memory** | 2.3 GB | 4 GB |
| **Storage** | 1 GB (temp) | 5 GB |
| **Network** | 1 external route | Load balancer ready |

### **Supported Data Formats**
- ✅ **CSV**: Primary format, full feature support
- ✅ **JSON**: Structured data processing
- ⚠️ **Excel**: Basic support (.xlsx files)
- 🔄 **Extensible**: Easy to add new formats

### **CSC Integration Features**
- 🔐 **Authentication**: OpenStack Keystone (Swift protocol)
- 📦 **Storage**: CSC Allas object storage integration
- 🌐 **Deployment**: CSC Rahti (OpenShift 4.x) optimized
- 📊 **Monitoring**: Built-in logging and status reporting

## �📚 For Students: Getting Started

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

**Note**: Local testing uses Docker Compose with separate containers, while CSC Rahti deployment uses the optimized multi-container pod architecture.

```bash
# Build and run all services locally
docker-compose up -d

# Check if all 4 services are running
docker-compose ps
# Should show: data-ingest, data-clean, data-visualization, redis

# View real-time logs from all services
docker-compose logs -f

# View individual service logs
docker-compose logs data-ingest
docker-compose logs data-clean  
docker-compose logs data-visualization
docker-compose logs redis

# Access the dashboard
# Open browser to: http://localhost:8501

# Test the data pipeline
# 1. Check if data is being ingested: docker-compose logs data-ingest
# 2. Verify cleaning process: docker-compose logs data-clean
# 3. Access web interface to see visualizations

# Stop all services
docker-compose down
```

**Local vs Production Architecture:**
- **Local**: Separate Docker containers with Docker networking
- **CSC Rahti**: Multi-container pod with shared volumes and localhost networking
- **File Sharing**: Both use volume mounts, but production is more efficient

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
   # Replace YOUR_NUMBER with your CSC project number (e.g., 2001234)
   # Replace YOUR_PROJECT_NAME with a unique name (e.g., your-data-pipeline)
   oc new-project your-data-pipeline --description="csc_project: YOUR_NUMBER"
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

4. **Build container images from your GitHub repository:**

   Since the pipeline uses a multi-container pod architecture, we first need to build all the individual service images:

   ```bash
   # Build data-ingest service image
   oc new-app https://github.com/YOUR_USERNAME/data-analysis-pipeline-rahti.git \
     --context-dir=data-ingest \
     --name=data-ingest \
     --strategy=docker
   
   # Build data-clean service image  
   oc new-app https://github.com/YOUR_USERNAME/data-analysis-pipeline-rahti.git \
     --context-dir=data-clean \
     --name=data-clean \
     --strategy=docker
   
   # Build data-visualization service image
   oc new-app https://github.com/YOUR_USERNAME/data-analysis-pipeline-rahti.git \
     --context-dir=data-visualization \
     --name=data-visualization \
     --strategy=docker
   ```

   **Wait for builds to complete** (this may take 5-10 minutes):
   ```bash
   oc get builds --watch
   ```

5. **Delete the individual deployments (we'll use multi-container pod instead):**
   ```bash
   oc delete deployment data-ingest data-clean data-visualization 2>/dev/null || true
   oc delete service data-ingest data-clean data-visualization 2>/dev/null || true
   ```

6. **Deploy the multi-container pipeline pod:**
   ```bash
   # Apply the multi-container deployment
   oc apply -f k8s/data-pipeline-deployment.yaml
   
   # Create the service
   oc apply -f k8s/data-pipeline-service.yaml
   
   # Create the route for web access
   oc expose service data-pipeline --name=data-pipeline-route --port=8501
   ```

7. **Configure resource limits to avoid quota issues:**
   ```bash
   oc patch deployment data-pipeline -p '{
     "spec": {
       "template": {
         "spec": {
           "containers": [
             {"name": "redis", "resources": {"limits": {"cpu": "100m", "memory": "256Mi"}, "requests": {"cpu": "50m", "memory": "128Mi"}}},
             {"name": "data-ingest", "resources": {"limits": {"cpu": "200m", "memory": "512Mi"}, "requests": {"cpu": "100m", "memory": "256Mi"}}},
             {"name": "data-clean", "resources": {"limits": {"cpu": "300m", "memory": "768Mi"}, "requests": {"cpu": "150m", "memory": "384Mi"}}},
             {"name": "data-visualization", "resources": {"limits": {"cpu": "300m", "memory": "768Mi"}, "requests": {"cpu": "150m", "memory": "384Mi"}}}
           ]
         }
       }
     }
   }'
   ```

8. **Get your application URL:**
   ```bash
   oc get routes
   ```

   Your application will be available at: `http://data-pipeline-route-YOUR_PROJECT.2.rahtiapp.fi`

#### ✅ Verification Steps:

1. **Check pod status:**
   ```bash
   oc get pods
   # Should show 4/4 Running containers in data-pipeline pod
   ```

2. **Monitor the data pipeline:**
   ```bash
   # Check data ingestion logs
   oc logs deployment/data-pipeline -c data-ingest --tail=10
   
   # Check data cleaning logs  
   oc logs deployment/data-pipeline -c data-clean --tail=10
   
   # Check visualization service
   oc logs deployment/data-pipeline -c data-visualization --tail=5
   
   # Check Redis coordination
   oc logs deployment/data-pipeline -c redis --tail=5
   ```

3. **Verify shared data files:**
   ```bash
   oc exec deployment/data-pipeline -c data-clean -- ls -la /shared/data
   # Should show: raw_*.csv, cleaned_*.csv, summary_*.json
   ```

4. **Access the web dashboard:**
   - Open the route URL in your browser
   - You should see the Streamlit data visualization dashboard
   - The dashboard will show your processed data from CSC Allas

## 💡 How The Multi-Container Architecture Works

### **🔧 Technical Implementation**

The pipeline uses a **single-pod, multi-container architecture** where all services run together and share resources:

#### **Pod Structure:**
```yaml
Pod: data-pipeline
├── Container 1: redis (localhost:6379)
├── Container 2: data-ingest
├── Container 3: data-clean  
└── Container 4: data-visualization (port 8501)

Shared Resources:
├── Network: All containers communicate via localhost
├── Storage: /shared/data mounted in all containers
└── Environment: Shared environment variables
```

### **📊 Data Processing Flow**

#### **Stage 1: Data Ingestion**
```mermaid
CSC Allas → data-ingest → /shared/data/raw_*.csv → Redis Status Update
```

- **Trigger**: Runs every 15 minutes automatically
- **Input**: CSV/JSON files from your CSC Allas container
- **Processing**: Downloads → Validates → Basic cleaning → Format standardization
- **Output**: `raw_Electric_prices.csv` (or your data file name)
- **Coordination**: Updates processing status in Redis

#### **Stage 2: Data Cleaning**
```mermaid
/shared/data/raw_*.csv → data-clean → Advanced Processing → cleaned_*.csv + summary_*.json
```

- **Trigger**: Monitors `/shared/data` for new raw files
- **Processing**:
  - 🧹 **Data Quality Checks**: Missing values, duplicates, outliers
  - 📊 **Statistical Analysis**: Mean, median, standard deviation
  - 🔍 **Pattern Detection**: Trends, anomalies, correlations
  - 📈 **Feature Engineering**: New calculated columns, data types
- **Output**: 
  - `cleaned_Electric_prices.csv` - Clean, processed dataset
  - `summary_Electric_prices.json` - Quality report and metadata

#### **Stage 3: Visualization**
```mermaid
/shared/data/cleaned_*.csv → data-visualization → Streamlit Dashboard → Web Interface
```

- **Features**:
  - 📊 **Interactive Charts**: Line plots, histograms, scatter plots
  - 📋 **Data Tables**: Sortable, filterable data views
  - 📈 **Statistics Dashboard**: Key metrics and summaries
  - 🔄 **Real-time Updates**: Automatically refreshes when new data arrives

### **🚀 Why Multi-Container Pod Architecture?**

#### **✅ Advantages:**
1. **Shared Storage**: All containers access the same `/shared/data` directory
2. **Fast Communication**: `localhost` networking (no network latency)
3. **Resource Efficiency**: Single pod scheduling and resource allocation
4. **Simplified Deployment**: One YAML file instead of multiple services
5. **Atomic Scaling**: All services scale together as a unit
6. **Development Friendly**: Easy to debug and monitor all services together

#### **📋 Container Responsibilities:**

| Container | CPU | Memory | Purpose |
|-----------|-----|---------|----------|
| **redis** | 100m | 256Mi | 🔄 Coordination, status tracking, caching |
| **data-ingest** | 200m | 512Mi | 📥 CSC Allas integration, file download |
| **data-clean** | 300m | 768Mi | 🧹 Heavy data processing, quality checks |
| **data-visualization** | 300m | 768Mi | 📊 Streamlit web app, charts, UI |

### **🔄 Service Coordination**

The services coordinate through:

1. **Shared File System**: 
   - Raw data: `/shared/data/raw_*.csv`
   - Processed data: `/shared/data/cleaned_*.csv` 
   - Reports: `/shared/data/summary_*.json`

2. **Redis Coordination**:
   - Processing status tracking
   - File metadata storage
   - Inter-service messaging

3. **Environment Variables**:
   - `SHARED_DATA_PATH=/shared/data`
   - `REDIS_HOST=localhost`
   - `REDIS_PORT=6379`

### **📈 Resource Management**

The deployment is optimized for CSC Rahti resource quotas:

- **Total CPU**: 900m (0.9 cores)
- **Total Memory**: ~2.3GB
- **Storage**: EmptyDir (ephemeral, but sufficient for data processing)
- **Network**: Internal pod networking + external route for web access

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

---

## 🎉 Production Status: FULLY OPERATIONAL

### ✅ **Working Multi-Container Pipeline**

This repository contains a **production-ready, fully operational** data analysis pipeline that has been successfully tested and deployed on CSC Rahti. 

#### **🚀 Confirmed Working Features:**

1. **📥 Data Ingestion**: 
   - ✅ Successfully connects to CSC Allas using Swift protocol
   - ✅ Downloads files (tested with `Electric_prices.csv`, 860KB → 2.1MB processed)
   - ✅ Automatic 15-minute ingestion cycles
   - ✅ Processes 23,040+ rows successfully

2. **🧹 Data Cleaning**:
   - ✅ Real-time file monitoring via shared volume
   - ✅ Advanced data quality checks (outlier detection, datetime conversion)  
   - ✅ Statistical processing and feature engineering
   - ✅ Generates comprehensive quality reports

3. **📊 Data Visualization**:
   - ✅ Interactive Streamlit web dashboard
   - ✅ Real-time data visualization updates
   - ✅ Accessible via public route: `http://data-pipeline-route-your-project.2.rahtiapp.fi`

4. **🏗️ Multi-Container Architecture**:
   - ✅ Single pod with 4 containers (Redis + 3 services)
   - ✅ Shared volume (`/shared/data`) working perfectly
   - ✅ Inter-service communication via localhost
   - ✅ Optimized resource usage (0.9 CPU cores, 2.3GB memory)

#### **📈 Proven Performance:**
- **Data Processing**: 23,040 rows processed in seconds
- **File Sharing**: Raw → Cleaned → Visualization pipeline working seamlessly
- **Resource Efficiency**: Runs within CSC Rahti quotas
- **Reliability**: Auto-restart, error handling, status monitoring

#### **🎓 Educational Value:**
- **Real-world Cloud Deployment**: Production OpenShift/Kubernetes environment
- **Modern Container Architecture**: Multi-container pods with shared storage
- **CSC Integration**: Actual CSC Allas and CSC Rahti platform usage
- **DevOps Pipeline**: GitHub → Build → Deploy → Monitor workflow
- **Data Engineering**: Complete ETL pipeline with quality assurance

### **🌟 Ready for Student Use**

Students can fork this repository and have a **working data analysis pipeline** deployed on CSC Rahti within 30 minutes, processing their own data from CSC Allas and visualizing results through an interactive web dashboard.

**Live Demo**: The pipeline is currently processing electricity price data and generating real-time visualizations accessible via the web interface.

---

*Last Updated: September 17, 2025 | Status: Production Ready ✅*

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
