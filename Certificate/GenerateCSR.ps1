Install-Module Microsoft.AzureStack.ReadinessChecker -Force
Import-Module Microsoft.AzureStack.ReadinessChecker
Update-Module Microsoft.AzureStack.ReadinessChecker

$subjectHash = [ordered]@{"OU"="AzureStack";"O"="HCCJP";"L"="Minato-ku";"ST"="Tokyo";"C"="JP"}
$outputDirectory = "c:\AzureStackCSR"
$IdentitySystem = "AAD"
$regionName = 'iijhuawei'
$externalFQDN = 'hccjp.org'

if((Test-Path $outputDirectory) -eq $false)
{
    New-Item -Path $outputDirectory -ItemType Directory -Force
}

Start-AzsReadinessChecker -RegionName $regionName -FQDN $externalFQDN -subject $subjectHash -RequestType SingleCSR -OutputRequestPath $OutputDirectory -IdentitySystem $IdentitySystem -IncludePaaS
