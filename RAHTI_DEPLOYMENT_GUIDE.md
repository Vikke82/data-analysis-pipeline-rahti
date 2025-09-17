# CSC Rahti Deployment Guide

## Prerequisites

1. **Access to CSC Rahti**: Ensure your project has Rahti access enabled
2. **OpenShift CLI**: Install `oc` command-line tool
3. **Docker Images**: Push your images to a container registry

## Step 1: Prepare Container Images

### Option A: Use Rahti's Integrated Registry
```bash
# Login to CSC Rahti
oc login https://api.2.rahti.csc.fi:6443

# Create a new project (replace YOUR_NUMBER with your CSC project number)
oc new-project your-data-pipeline --description="csc_project: YOUR_NUMBER"

# Use Rahti's integrated registry
docker tag dataanalysispipelinecontainer-data-ingest image-registry.rahti.csc.fi/your-data-pipeline/data-ingest:latest
docker tag dataanalysispipelinecontainer-data-clean image-registry.rahti.csc.fi/your-data-pipeline/data-clean:latest
docker tag dataanalysispipelinecontainer-data-visualization image-registry.rahti.csc.fi/your-data-pipeline/data-visualization:latest

# Push images
docker push image-registry.rahti.csc.fi/your-data-pipeline/data-ingest:latest
docker push image-registry.rahti.csc.fi/your-data-pipeline/data-clean:latest
docker push image-registry.rahti.csc.fi/your-data-pipeline/data-visualization:latest
```

### Option B: Use Docker Hub or Other Registry
```bash
# Tag for Docker Hub (replace 'yourusername' with your Docker Hub username)
docker tag dataanalysispipelinecontainer-data-ingest yourusername/data-pipeline-ingest:latest
docker tag dataanalysispipelinecontainer-data-clean yourusername/data-pipeline-clean:latest
docker tag dataanalysispipelinecontainer-data-visualization yourusername/data-pipeline-viz:latest

# Push to Docker Hub
docker push yourusername/data-pipeline-ingest:latest
docker push yourusername/data-pipeline-clean:latest
docker push yourusername/data-pipeline-viz:latest
```

## Step 2: Handle Allas Credentials Securely

### Create OpenShift Secret for Allas Credentials
```bash
# Create secret with your Allas credentials
oc create secret generic allas-credentials \
  --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 \
  --from-literal=OS_USERNAME=villemaj \
  --from-literal=OS_PASSWORD=your-password \
  --from-literal=OS_PROJECT_NAME=project_2015319 \
  --from-literal=OS_PROJECT_DOMAIN_NAME=Default \
  --from-literal=OS_USER_DOMAIN_NAME=Default \
  --from-literal=DATA_BUCKET=cloudservices
```

### Alternative: Use Application Credentials (More Secure)
```bash
# First, create application credentials on CSC (recommended for production)
# Then create secret with application credentials
oc create secret generic allas-app-credentials \
  --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 \
  --from-literal=OS_APPLICATION_CREDENTIAL_ID=your-app-cred-id \
  --from-literal=OS_APPLICATION_CREDENTIAL_SECRET=your-app-cred-secret \
  --from-literal=DATA_BUCKET=cloudservices
```

## Step 3: Deploy Services

Create Kubernetes/OpenShift manifests for each service:

### Redis Deployment
```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis
```

### Data Ingestion Service
```yaml
# data-ingest-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-ingest
spec:
  replicas: 1
  selector:
    matchLabels:
      app: data-ingest
  template:
    metadata:
      labels:
        app: data-ingest
    spec:
      containers:
      - name: data-ingest
        image: image-registry.rahti.csc.fi/your-data-pipeline/data-ingest:latest
        envFrom:
        - secretRef:
            name: allas-credentials
        volumeMounts:
        - name: shared-data
          mountPath: /shared/data
      volumes:
      - name: shared-data
        persistentVolumeClaim:
          claimName: shared-data-pvc
```

### Data Cleaning Service
```yaml
# data-clean-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-clean
spec:
  replicas: 1
  selector:
    matchLabels:
      app: data-clean
  template:
    metadata:
      labels:
        app: data-clean
    spec:
      containers:
      - name: data-clean
        image: image-registry.rahti.csc.fi/your-data-pipeline/data-clean:latest
        volumeMounts:
        - name: shared-data
          mountPath: /shared/data
      volumes:
      - name: shared-data
        persistentVolumeClaim:
          claimName: shared-data-pvc
```

### Data Visualization Service
```yaml
# data-visualization-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-visualization
spec:
  replicas: 1
  selector:
    matchLabels:
      app: data-visualization
  template:
    metadata:
      labels:
        app: data-visualization
    spec:
      containers:
      - name: data-visualization
        image: image-registry.rahti.csc.fi/your-data-pipeline/data-visualization:latest
        ports:
        - containerPort: 8501
        volumeMounts:
        - name: shared-data
          mountPath: /shared/data
      volumes:
      - name: shared-data
        persistentVolumeClaim:
          claimName: shared-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: data-visualization
spec:
  ports:
  - port: 8501
    targetPort: 8501
  selector:
    app: data-visualization
---
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: data-visualization
spec:
  port:
    targetPort: 8501
  to:
    kind: Service
    name: data-visualization
  tls:
    termination: edge
```

### Persistent Volume for Shared Data
```yaml
# persistent-volume.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data-pvc
spec:
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard-rwo
```

## Step 4: Deploy to Rahti

```bash
# Apply all manifests
oc apply -f redis-deployment.yaml
oc apply -f persistent-volume.yaml
oc apply -f data-ingest-deployment.yaml
oc apply -f data-clean-deployment.yaml
oc apply -f data-visualization-deployment.yaml

# Check deployment status
oc get pods
oc get routes

# View logs
oc logs -f deployment/data-ingest
oc logs -f deployment/data-clean
oc logs -f deployment/data-visualization
```

## Step 5: Security Best Practices for Allas

### 1. Use Application Credentials (Recommended)
- Create application credentials in CSC's web interface
- These can be revoked independently of your main account
- Limited scope and permissions

### 2. Use Sealed Secrets (Advanced)
```bash
# Install sealed-secrets controller (if available)
# Create sealed secret that only the cluster can decrypt
echo -n 'your-password' | oc create secret generic allas-sealed \
  --dry-run=client -o yaml \
  --from-file=password=/dev/stdin | \
  kubeseal -o yaml > allas-sealed-secret.yaml
```

### 3. Environment-Specific Secrets
```bash
# Create different secrets for different environments
oc create secret generic allas-prod \
  --from-literal=OS_USERNAME=prod-user \
  --from-literal=OS_PASSWORD=prod-password

oc create secret generic allas-dev \
  --from-literal=OS_USERNAME=dev-user \
  --from-literal=OS_PASSWORD=dev-password
```

## Step 6: Monitoring and Scaling

### Add Resource Limits
```yaml
resources:
  limits:
    memory: "1Gi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "100m"
```

### Enable Horizontal Pod Autoscaling
```bash
oc autoscale deployment data-visualization --min=1 --max=3 --cpu-percent=70
```

### Add Health Checks
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8501
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8501
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Step 7: Access Your Application

After deployment, get the route URL:
```bash
oc get routes
```

Your Streamlit dashboard will be available at:
`https://data-visualization-your-project.rahti.csc.fi`

## Troubleshooting

1. **Check pod status**: `oc get pods`
2. **View logs**: `oc logs -f pod-name`
3. **Debug pod**: `oc exec -it pod-name -- /bin/bash`
4. **Check secrets**: `oc get secrets`
5. **Verify mounts**: `oc describe pod pod-name`

## Cost Optimization

1. **Use appropriate resource requests/limits**
2. **Scale down during off-hours**
3. **Use persistent volumes efficiently**
4. **Monitor resource usage**: `oc top pods`

This deployment will give you a production-ready, scalable data analysis pipeline on CSC Rahti with secure Allas integration!
