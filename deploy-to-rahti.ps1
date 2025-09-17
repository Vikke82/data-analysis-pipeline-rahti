# PowerShell deployment script for CSC Rahti

Write-Host "🚀 Deploying Data Analysis Pipeline to CSC Rahti" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Check if oc is installed
if (-not (Get-Command oc -ErrorAction SilentlyContinue)) {
    Write-Host "❌ OpenShift CLI (oc) not found. Please install it first." -ForegroundColor Red
    Write-Host "   Download from: https://mirror.openshift.com/pub/openshift-v4/clients/oc/" -ForegroundColor Yellow
    exit 1
}

# Check if logged in
try {
    $currentUser = oc whoami 2>$null
    if (-not $currentUser) {
        throw "Not logged in"
    }
} catch {
    Write-Host "❌ Not logged in to OpenShift. Please run:" -ForegroundColor Red
    Write-Host "   oc login https://api.2.rahti.csc.fi:6443" -ForegroundColor Yellow
    exit 1
}

# Get current project
try {
    $project = oc project -q 2>$null
    if (-not $project) {
        throw "No project selected"
    }
} catch {
    Write-Host "❌ No project selected. Please create or select a project:" -ForegroundColor Red
    Write-Host "   oc new-project your-data-pipeline" -ForegroundColor Yellow
    exit 1
}

Write-Host "📁 Using project: $project" -ForegroundColor Cyan

# Prompt for registry choice
Write-Host ""
Write-Host "🐳 Container Registry Options:" -ForegroundColor Yellow
Write-Host "1. CSC Rahti Integrated Registry (recommended)" -ForegroundColor White
Write-Host "2. Docker Hub" -ForegroundColor White
Write-Host "3. Other registry" -ForegroundColor White
$registryChoice = Read-Host "Choose registry option (1-3)"

switch ($registryChoice) {
    "1" {
        $registry = "image-registry.apps.2.rahti.csc.fi/$project"
        Write-Host "Using Rahti integrated registry: $registry" -ForegroundColor Green
    }
    "2" {
        $dockerUser = Read-Host "Enter your Docker Hub username"
        $registry = "docker.io/$dockerUser"
        Write-Host "Using Docker Hub registry: $registry" -ForegroundColor Green
    }
    "3" {
        $customRegistry = Read-Host "Enter your registry URL"
        $registry = $customRegistry
        Write-Host "Using custom registry: $registry" -ForegroundColor Green
    }
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}

# Check if Allas credentials secret exists
try {
    oc get secret allas-credentials 2>$null | Out-Null
    Write-Host "✅ Allas credentials secret already exists" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "🔑 Creating Allas credentials secret..." -ForegroundColor Yellow
    Write-Host "Please provide your CSC Allas credentials:" -ForegroundColor Yellow
    
    $osUsername = Read-Host "OS_USERNAME (CSC username)"
    $osPassword = Read-Host "OS_PASSWORD (CSC password)" -AsSecureString
    $osPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($osPassword))
    $osProjectName = Read-Host "OS_PROJECT_NAME (e.g., project_2015319)"
    $dataBucket = Read-Host "DATA_BUCKET (container name, default: cloudservices)"
    if (-not $dataBucket) { $dataBucket = "cloudservices" }
    
    oc create secret generic allas-credentials `
        --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 `
        --from-literal=OS_USERNAME="$osUsername" `
        --from-literal=OS_PASSWORD="$osPasswordPlain" `
        --from-literal=OS_PROJECT_NAME="$osProjectName" `
        --from-literal=OS_PROJECT_DOMAIN_NAME=Default `
        --from-literal=OS_USER_DOMAIN_NAME=Default `
        --from-literal=DATA_BUCKET="$dataBucket"
    
    Write-Host "✅ Allas credentials secret created" -ForegroundColor Green
}

# Update deployment files with correct registry
Write-Host ""
Write-Host "📝 Updating deployment files with registry: $registry" -ForegroundColor Yellow

# Update image references in deployment files
(Get-Content k8s/data-ingest-deployment.yaml) -replace 'image-registry\.rahti\.csc\.fi/your-project', $registry | Set-Content k8s/data-ingest-deployment.yaml
(Get-Content k8s/data-clean-deployment.yaml) -replace 'image-registry\.rahti\.csc\.fi/your-project', $registry | Set-Content k8s/data-clean-deployment.yaml
(Get-Content k8s/data-visualization-deployment.yaml) -replace 'image-registry\.rahti\.csc\.fi/your-project', $registry | Set-Content k8s/data-visualization-deployment.yaml

# Deploy resources
Write-Host ""
Write-Host "🚀 Deploying resources to OpenShift..." -ForegroundColor Green

Write-Host "   📦 Creating ConfigMap..." -ForegroundColor White
oc apply -f k8s/configmap.yaml

Write-Host "   💾 Creating Persistent Volume..." -ForegroundColor White
oc apply -f k8s/persistent-volume.yaml

Write-Host "   🗄️  Deploying Redis..." -ForegroundColor White
oc apply -f k8s/redis-deployment.yaml

Write-Host "   📥 Deploying Data Ingest service..." -ForegroundColor White
oc apply -f k8s/data-ingest-deployment.yaml

Write-Host "   🧹 Deploying Data Clean service..." -ForegroundColor White
oc apply -f k8s/data-clean-deployment.yaml

Write-Host "   📊 Deploying Data Visualization service..." -ForegroundColor White
oc apply -f k8s/data-visualization-deployment.yaml

# Wait for deployments to be ready
Write-Host ""
Write-Host "⏳ Waiting for deployments to be ready..." -ForegroundColor Yellow
oc rollout status deployment/redis --timeout=300s
oc rollout status deployment/data-ingest --timeout=300s
oc rollout status deployment/data-clean --timeout=300s
oc rollout status deployment/data-visualization --timeout=300s

# Get route URL
Write-Host ""
Write-Host "🌐 Getting application URL..." -ForegroundColor Yellow
try {
    $routeUrl = oc get route data-visualization -o jsonpath='{.spec.host}' 2>$null
    if ($routeUrl) {
        Write-Host "✅ Application deployed successfully!" -ForegroundColor Green
        Write-Host "🔗 Dashboard URL: https://$routeUrl" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  Route not found. Check with: oc get routes" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not get route URL. Check with: oc get routes" -ForegroundColor Yellow
}

# Show status
Write-Host ""
Write-Host "📋 Deployment Status:" -ForegroundColor Yellow
oc get pods -l app=redis
oc get pods -l app=data-ingest
oc get pods -l app=data-clean
oc get pods -l app=data-visualization

Write-Host ""
Write-Host "🎉 Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Yellow
Write-Host "   Check pods:        oc get pods" -ForegroundColor White
Write-Host "   View logs:         oc logs -f deployment/data-visualization" -ForegroundColor White
Write-Host "   Get routes:        oc get routes" -ForegroundColor White
Write-Host "   Scale up:          oc scale deployment/data-visualization --replicas=2" -ForegroundColor White
Write-Host "   Delete all:        oc delete -f k8s/" -ForegroundColor White
