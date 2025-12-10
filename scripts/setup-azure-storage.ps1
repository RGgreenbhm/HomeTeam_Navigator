#Requires -Version 5.1
<#
.SYNOPSIS
    Sets up Azure Blob Storage for Patient_Explorer workspace sync.

.DESCRIPTION
    Creates all required Azure resources for secure PHI storage:
    - Resource Group
    - Storage Account (HIPAA-compliant settings)
    - Blob Containers
    - Key Vault (optional)
    - RBAC assignments

.NOTES
    Prerequisites:
    1. Azure CLI installed: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows
    2. Logged in: az login
    3. Correct subscription selected: az account set --subscription "Your Subscription"

.EXAMPLE
    .\setup-azure-storage.ps1
#>

param(
    [string]$ResourceGroup = "rg-patient-explorer",
    [string]$Location = "eastus2",
    [string]$StorageAccount = "stpatientexplorer",
    [string]$KeyVault = "kv-patient-explorer",
    [switch]$SkipKeyVault,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step { param($msg) Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "    ✓ $msg" -ForegroundColor Green }
function Write-Skip { param($msg) Write-Host "    - $msg (skipped)" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "    $msg" -ForegroundColor Gray }

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║     Patient_Explorer - Azure Storage Setup                   ║
║     HIPAA-Compliant Workspace Sync                          ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# Check Azure CLI
Write-Step "Checking prerequisites..."
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Success "Azure CLI v$($azVersion.'azure-cli') found"
} catch {
    Write-Host "`n    ERROR: Azure CLI not found!" -ForegroundColor Red
    Write-Host "    Install from: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    Write-Host "    Then run: az login" -ForegroundColor Yellow
    exit 1
}

# Check login status
$account = az account show --output json 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "`n    ERROR: Not logged in to Azure!" -ForegroundColor Red
    Write-Host "    Run: az login" -ForegroundColor Yellow
    exit 1
}
Write-Success "Logged in as: $($account.user.name)"
Write-Info "Subscription: $($account.name)"

if ($WhatIf) {
    Write-Host "`n[WhatIf Mode - No changes will be made]" -ForegroundColor Yellow
}

# ============================================================
# 1. Resource Group
# ============================================================
Write-Step "Creating Resource Group: $ResourceGroup"

$rgExists = az group exists --name $ResourceGroup
if ($rgExists -eq "true") {
    Write-Skip "Resource group already exists"
} elseif ($WhatIf) {
    Write-Info "Would create resource group in $Location"
} else {
    az group create `
        --name $ResourceGroup `
        --location $Location `
        --output none
    Write-Success "Created resource group"
}

# ============================================================
# 2. Storage Account
# ============================================================
Write-Step "Creating Storage Account: $StorageAccount"

$saExists = az storage account show --name $StorageAccount --resource-group $ResourceGroup 2>$null
if ($saExists) {
    Write-Skip "Storage account already exists"
} elseif ($WhatIf) {
    Write-Info "Would create storage account with HIPAA-compliant settings"
} else {
    az storage account create `
        --name $StorageAccount `
        --resource-group $ResourceGroup `
        --location $Location `
        --sku Standard_GRS `
        --kind StorageV2 `
        --https-only true `
        --min-tls-version TLS1_2 `
        --allow-blob-public-access false `
        --output none
    Write-Success "Created storage account"
}

# Enable blob versioning for .env file history
Write-Step "Enabling blob versioning..."
if ($WhatIf) {
    Write-Info "Would enable blob versioning"
} else {
    az storage account blob-service-properties update `
        --account-name $StorageAccount `
        --resource-group $ResourceGroup `
        --enable-versioning true `
        --output none
    Write-Success "Blob versioning enabled"
}

# ============================================================
# 3. Containers
# ============================================================
Write-Step "Creating blob containers..."

$containers = @(
    @{name="workspace-sync"; desc="Main sync container for all gitignored data"}
)

# Get storage key for container creation
$storageKey = (az storage account keys list --account-name $StorageAccount --resource-group $ResourceGroup --query "[0].value" -o tsv)

foreach ($container in $containers) {
    $containerExists = az storage container exists `
        --name $container.name `
        --account-name $StorageAccount `
        --account-key $storageKey `
        --query "exists" -o tsv

    if ($containerExists -eq "true") {
        Write-Skip "$($container.name) already exists"
    } elseif ($WhatIf) {
        Write-Info "Would create container: $($container.name)"
    } else {
        az storage container create `
            --name $container.name `
            --account-name $StorageAccount `
            --account-key $storageKey `
            --output none
        Write-Success "Created container: $($container.name)"
    }
}

# ============================================================
# 4. Key Vault (Optional)
# ============================================================
if (-not $SkipKeyVault) {
    Write-Step "Creating Key Vault: $KeyVault"

    $kvExists = az keyvault show --name $KeyVault --resource-group $ResourceGroup 2>$null
    if ($kvExists) {
        Write-Skip "Key vault already exists"
    } elseif ($WhatIf) {
        Write-Info "Would create key vault with soft-delete and purge protection"
    } else {
        az keyvault create `
            --name $KeyVault `
            --resource-group $ResourceGroup `
            --location $Location `
            --enable-soft-delete true `
            --enable-purge-protection true `
            --output none
        Write-Success "Created key vault"
    }
} else {
    Write-Step "Skipping Key Vault (--SkipKeyVault specified)"
}

# ============================================================
# 5. RBAC Assignments
# ============================================================
Write-Step "Configuring RBAC permissions..."

$admins = @(
    "rgreen@southviewteam.com",
    "rgreen@greenclinicteam.com",
    "autopilot@southviewteam.com"
)

$storageId = (az storage account show --name $StorageAccount --resource-group $ResourceGroup --query "id" -o tsv)

foreach ($admin in $admins) {
    Write-Info "Granting 'Storage Blob Data Contributor' to $admin..."
    if ($WhatIf) {
        Write-Info "  Would assign role"
    } else {
        # Check if user exists in tenant
        $userExists = az ad user show --id $admin 2>$null
        if ($userExists) {
            az role assignment create `
                --role "Storage Blob Data Contributor" `
                --assignee $admin `
                --scope $storageId `
                --output none 2>$null
            Write-Success "  Assigned to $admin"
        } else {
            Write-Skip "  User $admin not found in directory (may be in different tenant)"
        }
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                    Setup Complete!                           ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Host "Resources Created:" -ForegroundColor Cyan
Write-Host "  Resource Group:   $ResourceGroup"
Write-Host "  Storage Account:  $StorageAccount"
Write-Host "  Container:        workspace-sync"
if (-not $SkipKeyVault) {
    Write-Host "  Key Vault:        $KeyVault"
}
Write-Host "  Region:           $Location"

Write-Host "`nConnection String:" -ForegroundColor Cyan
$connStr = az storage account show-connection-string --name $StorageAccount --resource-group $ResourceGroup --query "connectionString" -o tsv
Write-Host "  $connStr" -ForegroundColor Gray

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Add Azure packages:  pip install azure-storage-blob azure-identity"
Write-Host "  2. Initialize sync:     python -m phase0 init-sync"
Write-Host "  3. Push data to Azure:  python -m phase0 sync-push"

Write-Host "`nStorage Account URL:" -ForegroundColor Cyan
Write-Host "  https://$StorageAccount.blob.core.windows.net" -ForegroundColor Gray

Write-Host ""
