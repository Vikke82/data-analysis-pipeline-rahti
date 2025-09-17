# CSC Rahti Deployment Checklist

## Prerequisites ✅

### 1. CSC Account Setup
- [ ] CSC account created and active
- [ ] Allas service activated
- [ ] Rahti service activated
- [ ] Test data uploaded to Allas container

### 2. Local Environment
- [ ] Docker installed and running
- [ ] OpenShift CLI (oc) installed
- [ ] PowerShell available
- [ ] Git configured

### 3. Project Files
- [ ] All container services tested locally
- [ ] Docker Compose working
- [ ] Kubernetes manifests created
- [ ] Deployment scripts ready

## Deployment Steps 📋

### Step 1: Login to CSC Rahti
```powershell
# Login to CSC Rahti
oc login https://api.2.rahti.csc.fi:6443

# Create a new project (replace YOUR_NUMBER with your CSC project number)
oc new-project your-data-pipeline-name --description="csc_project: YOUR_NUMBER"
```
**Status:** [ ] Complete

### Step 2: Manage Credentials
```powershell
# Run the credential management script
.\manage-allas-credentials.ps1
```
**Recommended:** Use option 5 (Application Credentials) for production
**Status:** [ ] Complete

### Step 3: Build and Push Images
```powershell
# Build and push Docker images to Rahti registry
.\build-and-push.ps1
```
**Status:** [ ] Complete

### Step 4: Deploy Pipeline
```powershell
# Deploy all services to Rahti
.\deploy-to-rahti.ps1
```
**Status:** [ ] Complete

### Step 5: Verify Deployment
```powershell
# Check all pods are running
oc get pods

# Check services
oc get services

# Check routes (external access)
oc get routes

# View logs if needed
oc logs -f deployment/data-visualization
```
**Status:** [ ] Complete

## Post-Deployment Verification 🔍

### Service Health Checks
- [ ] Data-ingest pod running and healthy
- [ ] Data-clean pod running and healthy
- [ ] Data-visualization pod running and healthy
- [ ] Redis pod running and healthy

### Connectivity Tests
- [ ] Data-ingest can connect to Allas
- [ ] Data-clean receives data from ingest
- [ ] Data-visualization displays processed data
- [ ] External route accessible

### Data Flow Verification
- [ ] Files downloaded from Allas
- [ ] Data processing completed
- [ ] Visualization frontend shows results
- [ ] Redis coordination working

## Troubleshooting Guide 🔧

### Common Issues and Solutions

#### 1. Pod Not Starting
```powershell
# Check pod status
oc describe pod <pod-name>

# Check logs
oc logs <pod-name>

# Common fixes:
# - Update resource limits in deployments
# - Check secret mounting
# - Verify image pull secrets
```

#### 2. Credential Issues
```powershell
# Test credentials
.\manage-allas-credentials.ps1
# Choose option 6 (Test connection)

# Update credentials if needed
# Choose option 2 (Update credentials)
```

#### 3. Route Not Accessible
```powershell
# Check route status
oc get routes

# Check service endpoints
oc get endpoints

# Verify service selector matches pod labels
oc describe service data-visualization
```

#### 4. Data Not Processing
```powershell
# Check data-ingest logs
oc logs -f deployment/data-ingest

# Check Redis connectivity
oc exec -it deployment/redis -- redis-cli ping

# Verify container/bucket exists in Allas
```

### Resource Scaling
If you need more resources:
```powershell
# Scale deployments
oc scale deployment data-clean --replicas=2

# Update resource requests/limits
oc edit deployment data-ingest
```

## Monitoring and Maintenance 📊

### Regular Checks
- [ ] Monitor resource usage in Rahti console
- [ ] Check application logs weekly
- [ ] Verify data processing results
- [ ] Update credentials as needed

### Updates and Rollbacks
```powershell
# Deploy new version
.\build-and-push.ps1
oc rollout restart deployment/data-ingest

# Rollback if needed
oc rollout undo deployment/data-ingest

# Check rollout status
oc rollout status deployment/data-ingest
```

### Backup Strategy
- [ ] Export Kubernetes configurations
- [ ] Backup processed data if needed
- [ ] Document custom configurations

## Security Best Practices 🔒

### Credentials Management
- [ ] Use application credentials (not main password)
- [ ] Regularly rotate credentials
- [ ] Monitor access logs in CSC portal
- [ ] Use separate credentials per environment

### Network Security
- [ ] Review route security settings
- [ ] Consider OAuth integration
- [ ] Monitor external access logs
- [ ] Update base images regularly

### Resource Protection
- [ ] Set appropriate resource limits
- [ ] Configure pod security policies
- [ ] Review RBAC permissions
- [ ] Enable audit logging

## Performance Optimization 🚀

### Resource Tuning
- [ ] Monitor CPU and memory usage
- [ ] Adjust resource requests/limits
- [ ] Scale replicas based on load
- [ ] Optimize container images

### Data Pipeline Efficiency
- [ ] Monitor processing times
- [ ] Optimize data transfer sizes
- [ ] Consider caching strategies
- [ ] Profile application performance

## Support and Documentation 📚

### CSC Resources
- [Rahti User Guide](https://docs.csc.fi/cloud/rahti/)
- [Allas User Guide](https://docs.csc.fi/data/Allas/)
- [CSC Service Status](https://status.csc.fi/)

### OpenShift Resources
- [OpenShift CLI Reference](https://docs.openshift.com/container-platform/4.11/cli_reference/openshift_cli/getting-started-cli.html)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

### Emergency Contacts
- CSC Service Desk: servicedesk@csc.fi
- Rahti Support: Available through CSC Service Desk

---

## Quick Command Reference 📝

```powershell
# Essential commands for daily operations

# Check pod status
oc get pods -w

# View logs
oc logs -f deployment/data-visualization

# Access pod shell
oc exec -it deployment/data-ingest -- /bin/bash

# Port forward for local testing
oc port-forward service/data-visualization 8501:8501

# Scale services
oc scale deployment data-clean --replicas=3

# Update image
oc set image deployment/data-ingest data-ingest=new-image:tag

# Check resource usage
oc top pods
```

Remember: Always test changes in a development environment first!
