# CSC Allas Credentials Management for Rahti Deployment

Write-Host "🔐 CSC Allas Credentials Management for Rahti" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

Write-Host ""
Write-Host "This script helps you securely manage Allas credentials for Rahti deployment." -ForegroundColor Cyan
Write-Host ""

# Check if oc is available
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
    Write-Host "✅ Logged in as: $currentUser" -ForegroundColor Green
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
    Write-Host "📁 Using project: $project" -ForegroundColor Cyan
} catch {
    Write-Host "❌ No project selected. Please create or select a project:" -ForegroundColor Red
    Write-Host "   oc new-project your-data-pipeline" -ForegroundColor Yellow
    exit 1
}

# Menu for credential management
Write-Host ""
Write-Host "🔧 Credential Management Options:" -ForegroundColor Yellow
Write-Host "1. Create new Allas credentials secret" -ForegroundColor White
Write-Host "2. Update existing credentials secret" -ForegroundColor White
Write-Host "3. View current credentials (masked)" -ForegroundColor White
Write-Host "4. Delete credentials secret" -ForegroundColor White
Write-Host "5. Create application credentials (recommended)" -ForegroundColor White
Write-Host "6. Test Allas connection" -ForegroundColor White

$choice = Read-Host "Choose option (1-6)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🔑 Creating new Allas credentials secret..." -ForegroundColor Yellow
        
        # Check if secret already exists
        try {
            oc get secret allas-credentials 2>$null | Out-Null
            Write-Host "⚠️  Secret 'allas-credentials' already exists!" -ForegroundColor Yellow
            $overwrite = Read-Host "Do you want to delete and recreate it? (y/n)"
            if ($overwrite -eq "y") {
                oc delete secret allas-credentials
                Write-Host "✅ Deleted existing secret" -ForegroundColor Green
            } else {
                Write-Host "❌ Aborted" -ForegroundColor Red
                exit 0
            }
        } catch {
            # Secret doesn't exist, continue
        }
        
        Write-Host ""
        Write-Host "Please provide your CSC Allas credentials:" -ForegroundColor Cyan
        Write-Host "(These will be stored securely in OpenShift)" -ForegroundColor Gray
        Write-Host ""
        
        $osUsername = Read-Host "OS_USERNAME (your CSC username)"
        $osPassword = Read-Host "OS_PASSWORD (your CSC password)" -AsSecureString
        $osPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($osPassword))
        $osProjectName = Read-Host "OS_PROJECT_NAME (e.g., project_2015319)"
        $dataBucket = Read-Host "DATA_BUCKET (container name, default: cloudservices)"
        if (-not $dataBucket) { $dataBucket = "cloudservices" }
        
        # Create the secret
        oc create secret generic allas-credentials `
            --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 `
            --from-literal=OS_USERNAME="$osUsername" `
            --from-literal=OS_PASSWORD="$osPasswordPlain" `
            --from-literal=OS_PROJECT_NAME="$osProjectName" `
            --from-literal=OS_PROJECT_DOMAIN_NAME=Default `
            --from-literal=OS_USER_DOMAIN_NAME=Default `
            --from-literal=DATA_BUCKET="$dataBucket"
        
        Write-Host "✅ Allas credentials secret created successfully" -ForegroundColor Green
    }
    
    "2" {
        Write-Host ""
        Write-Host "🔄 Updating existing credentials secret..." -ForegroundColor Yellow
        
        # Check if secret exists
        try {
            oc get secret allas-credentials 2>$null | Out-Null
        } catch {
            Write-Host "❌ Secret 'allas-credentials' does not exist. Use option 1 to create it." -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Which credential do you want to update?" -ForegroundColor Cyan
        Write-Host "1. Username" -ForegroundColor White
        Write-Host "2. Password" -ForegroundColor White
        Write-Host "3. Project Name" -ForegroundColor White
        Write-Host "4. Data Bucket" -ForegroundColor White
        
        $updateChoice = Read-Host "Choose option (1-4)"
        
        switch ($updateChoice) {
            "1" {
                $newUsername = Read-Host "Enter new username"
                oc patch secret allas-credentials -p="{`"data`":{`"OS_USERNAME`":`"$([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($newUsername)))`"}}"
                Write-Host "✅ Username updated" -ForegroundColor Green
            }
            "2" {
                $newPassword = Read-Host "Enter new password" -AsSecureString
                $newPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($newPassword))
                oc patch secret allas-credentials -p="{`"data`":{`"OS_PASSWORD`":`"$([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($newPasswordPlain)))`"}}"
                Write-Host "✅ Password updated" -ForegroundColor Green
            }
            "3" {
                $newProject = Read-Host "Enter new project name"
                oc patch secret allas-credentials -p="{`"data`":{`"OS_PROJECT_NAME`":`"$([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($newProject)))`"}}"
                Write-Host "✅ Project name updated" -ForegroundColor Green
            }
            "4" {
                $newBucket = Read-Host "Enter new data bucket name"
                oc patch secret allas-credentials -p="{`"data`":{`"DATA_BUCKET`":`"$([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($newBucket)))`"}}"
                Write-Host "✅ Data bucket updated" -ForegroundColor Green
            }
            default {
                Write-Host "❌ Invalid choice" -ForegroundColor Red
            }
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "👀 Current credentials (masked)..." -ForegroundColor Yellow
        
        try {
            $secret = oc get secret allas-credentials -o json | ConvertFrom-Json
            $data = $secret.data
            
            Write-Host ""
            Write-Host "OS_AUTH_URL: $([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($data.OS_AUTH_URL)))" -ForegroundColor Cyan
            Write-Host "OS_USERNAME: $([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($data.OS_USERNAME)))" -ForegroundColor Cyan
            $password = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($data.OS_PASSWORD))
            Write-Host "OS_PASSWORD: $('*' * $password.Length)" -ForegroundColor Cyan
            Write-Host "OS_PROJECT_NAME: $([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($data.OS_PROJECT_NAME)))" -ForegroundColor Cyan
            Write-Host "OS_PROJECT_DOMAIN_NAME: $([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($data.OS_PROJECT_DOMAIN_NAME)))" -ForegroundColor Cyan
            Write-Host "OS_USER_DOMAIN_NAME: $([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($data.OS_USER_DOMAIN_NAME)))" -ForegroundColor Cyan
            Write-Host "DATA_BUCKET: $([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($data.DATA_BUCKET)))" -ForegroundColor Cyan
        } catch {
            Write-Host "❌ Secret 'allas-credentials' not found" -ForegroundColor Red
        }
    }
    
    "4" {
        Write-Host ""
        Write-Host "🗑️  Deleting credentials secret..." -ForegroundColor Yellow
        
        try {
            oc get secret allas-credentials 2>$null | Out-Null
            $confirm = Read-Host "Are you sure you want to delete the credentials secret? (y/n)"
            if ($confirm -eq "y") {
                oc delete secret allas-credentials
                Write-Host "✅ Credentials secret deleted" -ForegroundColor Green
            } else {
                Write-Host "❌ Aborted" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Secret 'allas-credentials' not found" -ForegroundColor Red
        }
    }
    
    "5" {
        Write-Host ""
        Write-Host "🔐 Application Credentials Setup (Recommended for Production)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Application credentials are more secure than using your main CSC password." -ForegroundColor Cyan
        Write-Host "They can be revoked independently and have limited scope." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To create application credentials:" -ForegroundColor White
        Write-Host "1. Go to https://pouta.csc.fi" -ForegroundColor Gray
        Write-Host "2. Navigate to Identity > Application Credentials" -ForegroundColor Gray
        Write-Host "3. Click 'Create Application Credential'" -ForegroundColor Gray
        Write-Host "4. Give it a name (e.g., 'data-pipeline-rahti')" -ForegroundColor Gray
        Write-Host "5. Copy the ID and Secret" -ForegroundColor Gray
        Write-Host ""
        
        $hasAppCreds = Read-Host "Do you already have application credentials? (y/n)"
        
        if ($hasAppCreds -eq "y") {
            $appCredId = Read-Host "Application Credential ID"
            $appCredSecret = Read-Host "Application Credential Secret" -AsSecureString
            $appCredSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($appCredSecret))
            $dataBucket = Read-Host "DATA_BUCKET (container name, default: cloudservices)"
            if (-not $dataBucket) { $dataBucket = "cloudservices" }
            
            # Delete existing secret if it exists
            try {
                oc delete secret allas-credentials 2>$null
            } catch {
                # Ignore if doesn't exist
            }
            
            # Create new secret with application credentials
            oc create secret generic allas-credentials `
                --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 `
                --from-literal=OS_APPLICATION_CREDENTIAL_ID="$appCredId" `
                --from-literal=OS_APPLICATION_CREDENTIAL_SECRET="$appCredSecretPlain" `
                --from-literal=DATA_BUCKET="$dataBucket"
            
            Write-Host "✅ Application credentials secret created successfully" -ForegroundColor Green
        } else {
            Write-Host "Please create application credentials first using the steps above." -ForegroundColor Yellow
        }
    }
    
    "6" {
        Write-Host ""
        Write-Host "🧪 Testing Allas connection..." -ForegroundColor Yellow
        
        # Check if secret exists
        try {
            oc get secret allas-credentials 2>$null | Out-Null
        } catch {
            Write-Host "❌ Secret 'allas-credentials' not found. Create it first." -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Creating a test pod to verify Allas connection..." -ForegroundColor Cyan
        
        # Create a test pod
        $testPodManifest = @"
apiVersion: v1
kind: Pod
metadata:
  name: allas-test
spec:
  containers:
  - name: test
    image: python:3.11-slim
    command: ["/bin/bash"]
    args: ["-c", "pip install python-swiftclient python-keystoneclient && python -c 'from swiftclient.service import SwiftService; import os; print(f\"Testing connection to {os.environ.get(\"OS_PROJECT_NAME\", \"unknown project\")}\"); swift = SwiftService({\"os_auth_url\": os.environ[\"OS_AUTH_URL\"], \"os_username\": os.environ.get(\"OS_USERNAME\"), \"os_password\": os.environ.get(\"OS_PASSWORD\"), \"os_application_credential_id\": os.environ.get(\"OS_APPLICATION_CREDENTIAL_ID\"), \"os_application_credential_secret\": os.environ.get(\"OS_APPLICATION_CREDENTIAL_SECRET\"), \"os_project_name\": os.environ.get(\"OS_PROJECT_NAME\"), \"auth_version\": \"3\"}); list(swift.list()); print(\"✅ Connection successful!\")'"]
    envFrom:
    - secretRef:
        name: allas-credentials
  restartPolicy: Never
"@
        
        $testPodManifest | oc apply -f -
        
        Write-Host "Waiting for test to complete..." -ForegroundColor Cyan
        
        # Wait for pod to complete
        $timeout = 120
        $elapsed = 0
        while ($elapsed -lt $timeout) {
            $status = oc get pod allas-test -o jsonpath='{.status.phase}' 2>$null
            if ($status -eq "Succeeded") {
                Write-Host "✅ Test completed successfully!" -ForegroundColor Green
                oc logs allas-test
                break
            } elseif ($status -eq "Failed") {
                Write-Host "❌ Test failed!" -ForegroundColor Red
                oc logs allas-test
                break
            }
            Start-Sleep 5
            $elapsed += 5
        }
        
        if ($elapsed -ge $timeout) {
            Write-Host "⏰ Test timed out" -ForegroundColor Yellow
            oc logs allas-test
        }
        
        # Cleanup
        oc delete pod allas-test 2>$null
        Write-Host "🧹 Test pod cleaned up" -ForegroundColor Gray
    }
    
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔒 Security Recommendations:" -ForegroundColor Yellow
Write-Host "• Use application credentials instead of your main password" -ForegroundColor Gray
Write-Host "• Regularly rotate credentials" -ForegroundColor Gray
Write-Host "• Monitor access logs in CSC portal" -ForegroundColor Gray
Write-Host "• Use different credentials for different environments" -ForegroundColor Gray
Write-Host ""
