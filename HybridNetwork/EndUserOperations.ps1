.\CreateVNetForPeering.ps1 `
    -SubscriptionID "57847b98-1fc7-439a-97b7-2f5ac0121762" `
    -ResourceGroupName "UserResourceGroupName" `
    -Location "Japan East" `
    -VNetName "UserVNet" `
    -AddressPrefix '192.168.2.0/23' `
    -GuestUPN "admin_iijhccjp.onmicrosoft.com*" `
    -RemoteVirtualNetworkId '/subscriptions/6e4a9541-cf94-45a1-a613-5ae64c195bbb/resourceGroups/ERTest/providers/Microsoft.Network/virtualNetworks/ertest'
