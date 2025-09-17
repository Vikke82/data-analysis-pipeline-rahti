# Build and Push Docker Images Script for CSC Rahti

Write-Host "🐳 Building and Pushing Docker Images for CSC Rahti" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Prompt for registry choice
Write-Host ""
Write-Host "🐳 Container Registry Options:" -ForegroundColor Yellow
Write-Host "1. CSC Rahti Integrated Registry (recommended for CSC users)" -ForegroundColor White
Write-Host "2. Docker Hub (public registry)" -ForegroundColor White
Write-Host "3. Other registry" -ForegroundColor White
$registryChoice = Read-Host "Choose registry option (1-3)"

switch ($registryChoice) {
    "1" {
        $project = Read-Host "Enter your Rahti project name"
        $registry = "image-registry.apps.2.rahti.csc.fi/$project"
        Write-Host "Using Rahti integrated registry: $registry" -ForegroundColor Green
        
        # Login to Rahti registry
        Write-Host "🔐 Logging into Rahti registry..." -ForegroundColor Yellow
        Write-Host "Please ensure you're logged in to OpenShift first: oc login https://api.2.rahti.csc.fi:6443" -ForegroundColor Cyan
        $token = oc whoami -t
        if (-not $token) {
            Write-Host "❌ Not logged in to OpenShift. Please login first." -ForegroundColor Red
            exit 1
        }
        docker login -u unused -p $token image-registry.apps.2.rahti.csc.fi
    }
    "2" {
        $dockerUser = Read-Host "Enter your Docker Hub username"
        $registry = "docker.io/$dockerUser"
        Write-Host "Using Docker Hub registry: $registry" -ForegroundColor Green
        
        # Login to Docker Hub
        Write-Host "🔐 Logging into Docker Hub..." -ForegroundColor Yellow
        docker login docker.io
    }
    "3" {
        $customRegistry = Read-Host "Enter your registry URL"
        $registry = $customRegistry
        Write-Host "Using custom registry: $registry" -ForegroundColor Green
        
        # Login to custom registry
        Write-Host "🔐 Please ensure you're logged into your registry" -ForegroundColor Yellow
        $loginChoice = Read-Host "Do you need to login? (y/n)"
        if ($loginChoice -eq "y") {
            docker login $customRegistry
        }
    }
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}

# Build images
Write-Host ""
Write-Host "🔨 Building Docker images..." -ForegroundColor Yellow

Write-Host "   📥 Building data-ingest image..." -ForegroundColor White
docker build -t "$registry/data-ingest:latest" ./data-ingest/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build data-ingest image" -ForegroundColor Red
    exit 1
}

Write-Host "   🧹 Building data-clean image..." -ForegroundColor White
docker build -t "$registry/data-clean:latest" ./data-clean/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build data-clean image" -ForegroundColor Red
    exit 1
}

Write-Host "   📊 Building data-visualization image..." -ForegroundColor White
docker build -t "$registry/data-visualization:latest" ./data-visualization/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build data-visualization image" -ForegroundColor Red
    exit 1
}

# Push images
Write-Host ""
Write-Host "📤 Pushing Docker images to registry..." -ForegroundColor Yellow

Write-Host "   📥 Pushing data-ingest image..." -ForegroundColor White
docker push "$registry/data-ingest:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to push data-ingest image" -ForegroundColor Red
    exit 1
}

Write-Host "   🧹 Pushing data-clean image..." -ForegroundColor White
docker push "$registry/data-clean:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to push data-clean image" -ForegroundColor Red
    exit 1
}

Write-Host "   📊 Pushing data-visualization image..." -ForegroundColor White
docker push "$registry/data-visualization:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to push data-visualization image" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All images built and pushed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Images pushed:" -ForegroundColor Yellow
Write-Host "   $registry/data-ingest:latest" -ForegroundColor White
Write-Host "   $registry/data-clean:latest" -ForegroundColor White
Write-Host "   $registry/data-visualization:latest" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Now you can deploy using: .\deploy-to-rahti.ps1" -ForegroundColor Green
