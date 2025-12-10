# Azure Storage Setup via Portal

If you prefer using the Azure Portal instead of CLI/PowerShell, follow these steps.

## Prerequisites

1. Azure subscription with HIPAA BAA in place (Microsoft 365 Business)
2. Admin access to Azure Portal: https://portal.azure.com

---

## Step 1: Create Resource Group

1. Go to **Azure Portal** → **Resource groups** → **+ Create**
2. Fill in:
   - **Subscription**: Your subscription
   - **Resource group**: `rg-patient-explorer`
   - **Region**: `East US 2`
3. Click **Review + create** → **Create**

---

## Step 2: Create Storage Account

1. Go to **Storage accounts** → **+ Create**
2. **Basics** tab:
   - **Resource group**: `rg-patient-explorer`
   - **Storage account name**: `stpatientexplorer` (must be globally unique, lowercase)
   - **Region**: `East US 2`
   - **Performance**: Standard
   - **Redundancy**: Geo-redundant storage (GRS)

3. **Advanced** tab:
   - ✅ **Require secure transfer for REST API operations** (HTTPS only)
   - **Minimum TLS version**: Version 1.2
   - ❌ **Allow enabling anonymous access on individual containers** (UNCHECK this!)
   - ✅ **Enable blob versioning**

4. **Networking** tab:
   - **Network access**: Enable public access from all networks
     (We'll use Azure AD auth, not public anonymous access)
   - Or choose **Disable public access and use private access** for stricter security

5. **Data protection** tab:
   - ✅ **Enable soft delete for blobs** (7 days)
   - ✅ **Enable soft delete for containers** (7 days)
   - ✅ **Enable versioning for blobs**

6. Click **Review + create** → **Create**

---

## Step 3: Create Container

1. Open your new storage account `stpatientexplorer`
2. Go to **Data storage** → **Containers** → **+ Container**
3. Create container:
   - **Name**: `workspace-sync`
   - **Public access level**: Private (no anonymous access)
4. Click **Create**

---

## Step 4: Configure Access (RBAC)

1. In your storage account, go to **Access Control (IAM)**
2. Click **+ Add** → **Add role assignment**
3. Select role: **Storage Blob Data Contributor**
4. Click **Next**
5. Select **User, group, or service principal**
6. Click **+ Select members**
7. Search and add:
   - `rgreen@southviewteam.com`
   - `rgreen@greenclinicteam.com`
   - `autopilot@southviewteam.com`
8. Click **Review + assign**

---

## Step 5: (Optional) Create Key Vault

For customer-managed encryption keys:

1. Go to **Key vaults** → **+ Create**
2. Fill in:
   - **Resource group**: `rg-patient-explorer`
   - **Key vault name**: `kv-patient-explorer`
   - **Region**: `East US 2`
   - **Pricing tier**: Standard
3. **Access configuration**:
   - ✅ **Enable soft-delete**
   - ✅ **Enable purge protection**
4. Click **Review + create** → **Create**

---

## Step 6: Verify HIPAA Settings

Go to your storage account and verify these settings:

| Setting | Location | Required Value |
|---------|----------|----------------|
| Secure transfer | Configuration | Enabled |
| Minimum TLS | Configuration | 1.2 |
| Public access | Configuration | Disabled |
| Blob versioning | Data protection | Enabled |
| Soft delete | Data protection | Enabled |

---

## Step 7: Get Connection Info

For the Python sync client, you'll need:

1. **Storage Account Name**: `stpatientexplorer`
2. **Container Name**: `workspace-sync`

The Python client uses Azure AD authentication (your Microsoft account), so you don't need connection strings or access keys.

---

## Summary

| Resource | Value |
|----------|-------|
| Resource Group | `rg-patient-explorer` |
| Storage Account | `stpatientexplorer` |
| Container | `workspace-sync` |
| Region | East US 2 |
| Access | Azure AD RBAC |
| Encryption | Microsoft-managed (or Key Vault) |

---

## Next Steps

After creating resources:

```bash
# 1. Install Azure packages
pip install azure-storage-blob azure-identity

# 2. Initialize sync manifest
python -m phase0 init-sync

# 3. Test by pushing data
python -m phase0 sync-push
```

---

*Created: 2025-12-08*
