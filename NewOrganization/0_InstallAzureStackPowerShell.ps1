
$PSGallery = Get-PSRepository -Name "PSGallery"
if($PSGallery -eq $null) {
    Register-PsRepository -Default
    Set-PSRepository -Name "PSGallery" -InstallationPolicy Trusted
}
Import-Module -Name PowerShellGet -ErrorAction Stop
Import-Module -Name PackageManagement -ErrorAction Stop


#uninstall existing version for update
#Get-Module -Name Azs.* -ListAvailable | Uninstall-Module -Force -Verbose
#Get-Module -Name Azure* -ListAvailable | Uninstall-Module -Force -Verbose

# Install the AzureRM.Bootstrapper module. Select Yes when prompted to install NuGet
Install-Module -Name AzureRm.BootStrapper

# Install and import the API Version Profile required by Azure Stack into the current PowerShell session.
Use-AzureRmProfile -Profile 2018-03-01-hybrid -Force

Install-Module -Name AzureStack -RequiredVersion 1.6.0
