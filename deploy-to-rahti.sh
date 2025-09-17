#!/bin/bash
# Deployment script for CSC Rahti

set -e

echo "🚀 Deploying Data Analysis Pipeline to CSC Rahti"
echo "================================================="

# Check if oc is installed
if ! command -v oc &> /dev/null; then
    echo "❌ OpenShift CLI (oc) not found. Please install it first."
    echo "   Download from: https://mirror.openshift.com/pub/openshift-v4/clients/oc/"
    exit 1
fi

# Check if logged in
echo "🔍 Checking OpenShift login status..."
if ! oc whoami &> /dev/null; then
    echo "❌ Not logged into OpenShift. Please run:"
    echo "   oc login https://api.2.rahti.csc.fi:6443"
    exit 1
fi

# Get current project
PROJECT=$(oc project -q 2>/dev/null || echo "")
if [ -z "$PROJECT" ]; then
    echo "❌ No project selected. Please create or select a project:"
    echo "   oc new-project your-data-pipeline"
    exit 1
fi

echo "📁 Using project: $PROJECT"

# Prompt for registry choice
echo ""
echo "🐳 Container Registry Options:"
echo "1. CSC Rahti Integrated Registry (recommended)"
echo "2. Docker Hub"
echo "3. Other registry"
read -p "Choose registry option (1-3): " REGISTRY_CHOICE

case $REGISTRY_CHOICE in
    1)
        REGISTRY="image-registry.rahti.csc.fi/$PROJECT"
        echo "Using Rahti integrated registry: $REGISTRY"
        ;;
    2)
        read -p "Enter your Docker Hub username: " DOCKER_USER
        REGISTRY="docker.io/$DOCKER_USER"
        echo "Using Docker Hub registry: $REGISTRY"
        ;;
    3)
        read -p "Enter your registry URL: " CUSTOM_REGISTRY
        REGISTRY="$CUSTOM_REGISTRY"
        echo "Using custom registry: $REGISTRY"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Check if Allas credentials secret exists
if ! oc get secret allas-credentials &> /dev/null; then
    echo ""
    echo "🔑 Creating Allas credentials secret..."
    echo "Please provide your CSC Allas credentials:"
    
    read -p "OS_USERNAME (CSC username): " OS_USERNAME
    read -s -p "OS_PASSWORD (CSC password): " OS_PASSWORD
    echo ""
    read -p "OS_PROJECT_NAME (e.g., project_2015319): " OS_PROJECT_NAME
    read -p "DATA_BUCKET (container name, default: cloudservices): " DATA_BUCKET
    DATA_BUCKET=${DATA_BUCKET:-cloudservices}
    
    oc create secret generic allas-credentials \
        --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 \
        --from-literal=OS_USERNAME="$OS_USERNAME" \
        --from-literal=OS_PASSWORD="$OS_PASSWORD" \
        --from-literal=OS_PROJECT_NAME="$OS_PROJECT_NAME" \
        --from-literal=OS_PROJECT_DOMAIN_NAME=Default \
        --from-literal=OS_USER_DOMAIN_NAME=Default \
        --from-literal=DATA_BUCKET="$DATA_BUCKET"
    
    echo "✅ Allas credentials secret created"
else
    echo "✅ Allas credentials secret already exists"
fi

# Update deployment files with correct registry
echo ""
echo "📝 Updating deployment files with registry: $REGISTRY"

# Update image references in deployment files
sed -i.bak "s|image-registry.rahti.csc.fi/your-project|$REGISTRY|g" k8s/data-ingest-deployment.yaml
sed -i.bak "s|image-registry.rahti.csc.fi/your-project|$REGISTRY|g" k8s/data-clean-deployment.yaml
sed -i.bak "s|image-registry.rahti.csc.fi/your-project|$REGISTRY|g" k8s/data-visualization-deployment.yaml

# Deploy resources
echo ""
echo "🚀 Deploying resources to OpenShift..."

echo "   📦 Creating ConfigMap..."
oc apply -f k8s/configmap.yaml

echo "   💾 Creating Persistent Volume..."
oc apply -f k8s/persistent-volume.yaml

echo "   🗄️  Deploying Redis..."
oc apply -f k8s/redis-deployment.yaml

echo "   📥 Deploying Data Ingest service..."
oc apply -f k8s/data-ingest-deployment.yaml

echo "   🧹 Deploying Data Clean service..."
oc apply -f k8s/data-clean-deployment.yaml

echo "   📊 Deploying Data Visualization service..."
oc apply -f k8s/data-visualization-deployment.yaml

# Wait for deployments to be ready
echo ""
echo "⏳ Waiting for deployments to be ready..."
oc rollout status deployment/redis --timeout=300s
oc rollout status deployment/data-ingest --timeout=300s
oc rollout status deployment/data-clean --timeout=300s
oc rollout status deployment/data-visualization --timeout=300s

# Get route URL
echo ""
echo "🌐 Getting application URL..."
ROUTE_URL=$(oc get route data-visualization -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
if [ -n "$ROUTE_URL" ]; then
    echo "✅ Application deployed successfully!"
    echo "🔗 Dashboard URL: https://$ROUTE_URL"
else
    echo "⚠️  Route not found. Check with: oc get routes"
fi

# Show status
echo ""
echo "📋 Deployment Status:"
oc get pods -l app=redis
oc get pods -l app=data-ingest
oc get pods -l app=data-clean
oc get pods -l app=data-visualization

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📝 Useful commands:"
echo "   Check pods:        oc get pods"
echo "   View logs:         oc logs -f deployment/data-visualization"
echo "   Get routes:        oc get routes"
echo "   Scale up:          oc scale deployment/data-visualization --replicas=2"
echo "   Delete all:        oc delete -f k8s/"

# Restore backup files
mv k8s/data-ingest-deployment.yaml.bak k8s/data-ingest-deployment.yaml 2>/dev/null || true
mv k8s/data-clean-deployment.yaml.bak k8s/data-clean-deployment.yaml 2>/dev/null || true
mv k8s/data-visualization-deployment.yaml.bak k8s/data-visualization-deployment.yaml 2>/dev/null || true
