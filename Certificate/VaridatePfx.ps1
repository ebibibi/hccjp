Install-Module Microsoft.AzureStack.ReadinessChecker -force

New-Item C:\Certificates -ItemType Directory
$directories = 'ACSBlob','ACSQueue','ACSTable','Admin Portal','ARM Admin','ARM Public','KeyVault','KeyVaultInternal','Public Portal'
$destination = 'c:\certificates'
$directories | % { New-Item -Path (Join-Path $destination $PSITEM) -ItemType Directory -Force}

$pfxPassword = Read-Host -Prompt "Enter PFX Password" -AsSecureString 
Start-AzsReadinessChecker -CertificatePath c:\certificates -pfxPassword $pfxPassword -RegionName iijhuawei -FQDN hccjp.org -IdentitySystem AAD


#PaaS
$PaaSCertificates = @{
    'PaaSDBCert' = @{'pfxPath' = '<Path to DBAdapter PFX>';'pfxPassword' = (ConvertTo-SecureString -String '<Password for PFX>' -AsPlainText -Force)}
    'PaaSDefaultCert' = @{'pfxPath' = '<Path to Default PFX>';'pfxPassword' = (ConvertTo-SecureString -String '<Password for PFX>' -AsPlainText -Force)}
    'PaaSAPICert' = @{'pfxPath' = '<Path to API PFX>';'pfxPassword' = (ConvertTo-SecureString -String '<Password for PFX>' -AsPlainText -Force)}
    'PaaSFTPCert' = @{'pfxPath' = '<Path to FTP PFX>';'pfxPassword' = (ConvertTo-SecureString -String '<Password for PFX>' -AsPlainText -Force)}
    'PaaSSSOCert' = @{'pfxPath' = '<Path to SSO PFX>';'pfxPassword' = (ConvertTo-SecureString -String '<Password for PFX>' -AsPlainText -Force)}
    }

Start-AzsReadinessChecker -PaaSCertificates $PaaSCertificates -RegionName iijhuawei -FQDN hccjp.org
