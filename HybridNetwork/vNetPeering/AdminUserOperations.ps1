#Use Sponsorship12000USD
.\CreateVNetForPeering.ps1 `
    -SubscriptionID "6e4a9541-cf94-45a1-a613-5ae64c195bbb" `
    -ResourceGroupName "ERTest" `
    -Location "Japan East" `
    -VNetName "ertest" `
    -AddressPrefix '192.168.16.0/23' `
    -GuestUPN "admin_hccjp.org*" `
    -RemoteVirtualNetworkId '/subscriptions/57847b98-1fc7-439a-97b7-2f5ac0121762/resourceGroups/UserResourceGroupName/providers/Microsoft.Network/virtualNetworks/UserVNet' `
    -AdminOperation