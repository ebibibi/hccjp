Install-Module Microsoft.AzureStack.ReadinessChecker -Force

$subjectHash = [ordered]@{"OU"="AzureStack";"O"="HCCJP";"L"="Minato-ku";"ST"="Tokyo";"C"="JP"}
$outputDirectory = "c:\AzureStackCSR"
$IdentitySystem = "AAD"
$regionName = 'iijhuawei'
$externalFQDN = 'hccjp.org'

Start-AzsReadinessChecker -RegionName $regionName -FQDN $externalFQDN -subject $subjectHash -RequestType SingleCSR -OutputRequestPath $OutputDirectory -IdentitySystem $IdentitySystem -IncludePaaS
