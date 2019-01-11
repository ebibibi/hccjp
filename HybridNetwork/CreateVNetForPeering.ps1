Param (
    [parameter(mandatory=$true)]$SubscriptionID,
    [parameter(mandatory=$true)]$ResourceGroupName,
    $Location = "Japan East",
    [parameter(mandatory=$true)]$VNetName,
    [parameter(mandatory=$true)]$AddressPrefix,
    [parameter(mandatory=$true)]$GuestUPN,
    [parameter(mandatory=$true)]$RemoteVirtualNetworkId,
    [switch]$AdminOperation

)


# Select subscription
$subscription = Get-AzSubscription -SubscriptionId $SubscriptionID
if ($null -eq $subscription ) {
    Write-Host "サブスクリプションID: $SubscriptionID のサブスクリプションが存在しませんでした。"
    Write-Host "Connect-AzAccount コマンドレットで適切なアカウントで認証し、再度実行して下さい。"
    exit 1
}

Select-AzSubscription -Subscription $SubscriptionID

# Create a resource group.
New-AzResourceGroup -Name $ResourceGroupName -Location $Location -Force

# Create virtual network.
$vNet = Get-AzVirtualnetwork -ResourceGroupName $ResourceGroupName -Name $VNetName -ErrorAction SilentlyContinue
if ($null -eq $vNet) {
    $vNet = New-AzVirtualNetwork -ResourceGroupName $ResourceGroupName -Name $VNetName -AddressPrefix $AddressPrefix -Location $Location -Force
}

# Assign Guest permissions to VNet.
$GuestUser = Get-AzADUser | Where-Object {$_.UserPrincipalName -like $GuestUPN}
if ($null -eq $GuestUser) {
    Write-Host -ForegroundColor Red "$GuestUPN を持つユーザーがAAD内に見つかりませんでした。事前に招待を行っておく必要があります。"
    exit 1
}

$roleAssignment = Get-AzRoleAssignment `
    -ObjectId $GuestUser.Id `
    -RoleDefinitionName "Network Contributor" `
    -Scope "/subscriptions/$SubscriptionID/resourceGroups/$ResourceGroupName/providers/Microsoft.Network/VirtualNetworks/$VNetName" `
    -ErrorAction SilentlyContinue

if($null -eq $roleAssignment) {
    New-AzRoleAssignment `
        -ObjectId $GuestUser.Id `
        -RoleDefinitionName "Network Contributor" `
        -Scope "/subscriptions/$SubscriptionID/resourceGroups/$ResourceGroupName/providers/Microsoft.Network/VirtualNetworks/$VNetName"
}

# Create Peering
$peeringName = ("$VNetName" + "PeeringforHCCJP")
$peering = Get-AzVirtualNetworkPeering -VirtualNetworkName $VnetName -ResourceGroupName $ResourceGroupName -Name $peeringName -ErrorAction SilentlyContinue

if($null -eq $peering){
    if($AdminOperation) {
        #管理者側
        Add-AzVirtualNetworkPeering -Name $peeringName -VirtualNetwork $vNet -RemoteVirtualNetworkId $RemoteVirtualNetworkId -AllowForwardedTraffic -AllowGatewayTransit
    } else {
        #ユーザー側
        Add-AzVirtualNetworkPeering -Name $peeringName -VirtualNetwork $vNet -RemoteVirtualNetworkId $RemoteVirtualNetworkId -AllowForwardedTraffic -UseRemoteGateways
    }
}

Get-AzResource -ResourceId $vNet.Id
