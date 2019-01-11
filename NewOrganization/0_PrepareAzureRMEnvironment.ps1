# prepare azure stack powershell environment
$ArmEndpointforAdmin = "https://adminmanagement.iijhuawei.hccjp.org"
$ArmEndpointforUser = "https://management.iijhuawei.hccjp.org"
$GraphAudience = "https://graph.windows.net/"

# Register an AzureRM environment that targets your Azure Stack instance
Add-AzureRMEnvironment `
  -Name "AzureStackUser" `
  -ArmEndpoint $ArmEndpointforUser

Add-AzureRMEnvironment `
  -Name "AzureStackAdmin" `
  -ArmEndpoint $ArmEndpointforAdmin

Set-AzureRmEnvironment `
  -Name "AzureStackUser" `
  -GraphAudience $GraphAudience

Set-AzureRmEnvironment `
  -Name "AzureStackAdmin" `
  -GraphAudience $GraphAudience

#Login-AzureRmAccount -EnvironmentName "AzureCloud"
#Login-AzureRmAccount -EnvironmentName "AzureStackUser"
#Login-AzureRmAccount -EnvironmentName "AzureStackAdmin"