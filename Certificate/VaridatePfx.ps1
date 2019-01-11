Install-Module Microsoft.AzureStack.ReadinessChecker -force
update-module Microsoft.AzureStack.ReadinessChecker -force
New-Item C:\Certificates -ItemType Directory
New-Item C:\Certificates\AAD -ItemType Directory
$directories = 'ACSBlob','ACSQueue','ACSTable','Admin Portal','ARM Admin','ARM Public','KeyVault','KeyVaultInternal','Public Portal', 'Admin Extension Host', 'Public Extension Host'
$destination = 'C:\certificates\AAD'
$directories | ForEach-Object { New-Item -Path (Join-Path $destination $PSITEM) -ItemType Directory -Force}

$pfxPassword = Read-Host -Prompt "Enter PFX Password" -AsSecureString 

Invoke-AzsCertificateValidation -CertificatePath c:\certificates\AAD -pfxPassword $pfxPassword -RegionName iijhuawei -FQDN hccjp.org -IdentitySystem AAD

#PaaS
$PaaSCertificates = @{
    'PaaSDBCert' = @{'pfxPath' = 'C:\Certificates\AAD\Public Portal\portal.iijhuawei.hccjp.org.pfx';'pfxPassword' = $pfxPassword }
    'PaaSDefaultCert' = @{'pfxPath' = 'C:\Certificates\AAD\Public Portal\portal.iijhuawei.hccjp.org.pfx';'pfxPassword' = $pfxPassword }
    'PaaSAPICert' = @{'pfxPath' = 'C:\Certificates\AAD\Public Portal\portal.iijhuawei.hccjp.org.pfx';'pfxPassword' = $pfxPassword }
    'PaaSFTPCert' = @{'pfxPath' = 'C:\Certificates\AAD\Public Portal\portal.iijhuawei.hccjp.org.pfx';'pfxPassword' = $pfxPassword }
    'PaaSSSOCert' = @{'pfxPath' = 'C:\Certificates\AAD\Public Portal\portal.iijhuawei.hccjp.org.pfx';'pfxPassword' = $pfxPassword }
    }

Invoke-AzsCertificateValidation -PaaSCertificates $PaaSCertificates -RegionName iijhuawei -FQDN hccjp.org
