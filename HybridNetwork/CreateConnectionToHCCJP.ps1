#設定
$AuthorizationKey = ""                          #管理者から指定されたAuthorization Keyを入力します。
$AddressPrefix = '192.168.*.0/23'               #ここには管理者から指定されたネットワークアドレスを入力します
$SubnetAddressPrefix = '192.168.*.0/24'         #ここには管理者から指定されたネットワークアドレス内から選択したアドレスを入力します。
$GatewaySubnetAddressPrefix = '192.168.*.0/26'  #ここには管理者から指定されたネットワークアドレス内から選択したアドレスを入力します。

#ここから下は各種の名前ですので必要に応じて変更して下さい。変更は必須ではありません。
$ResourceGroupName = "HybridNetworkForHCCJP"
$Location = "japaneast"
$VNetName = "vnet"
$GWName = "GatewayForHCCJP"
$GWIPName = "GatewayIP"
$GWIPconfName = "gwipconf"

#リソースグループ作成
New-AzResourceGroup -Name $ResourceGroupName -Location $Location

#仮想ネットワーク作成
New-AzVirtualNetwork -Name $VnetName -ResourceGroupName $ResourceGroupName -Location $Location -AddressPrefix $AddressPrefix
$Vnet = Get-AzVirtualNetwork -Name $VnetName -ResourceGroupName $ResourceGroupName

#サブネット作成
$subnetConfig = Add-AzVirtualNetworkSubnetConfig -Name default -VirtualNetwork $Vnet -AddressPrefix $SubnetAddressPrefix 
$Vnet = $Vnet | Set-AzVirtualNetwork

#ゲートウェイサブネット作成
Add-AzVirtualNetworkSubnetConfig -Name GatewaySubnet -VirtualNetwork $Vnet -AddressPrefix $GatewaySubnetAddressPrefix
$Vnet = $Vnet | Set-AzVirtualNetwork
$getewaySubnet = Get-AzVirtualNetworkSubnetConfig -Name 'GatewaySubnet' -VirtualNetwork $Vnet

#パブリックIPアドレス取得
$pip = New-AzPublicIpAddress -Name $GWIPName  -ResourceGroupName $ResourceGroupName -Location $Location -AllocationMethod Dynamic

#ゲートウェイ作成
$ipconf = New-AzVirtualNetworkGatewayIpConfig -Name $GWIPconfName -Subnet $getewaySubnet -PublicIpAddress $pip
New-AzVirtualNetworkGateway -Name $GWName -ResourceGroupName $ResourceGroupName -Location $Location -IpConfigurations $ipconf -GatewayType Expressroute -GatewaySku Standard

#ExpressRouteとの接続
$id = "/subscriptions/44bc783b-d8d7-4a07-8af1-83cc11310ad3/resourceGroups/ExpressRoute/providers/Microsoft.Network/expressRouteCircuits/hccjp_expressroute"    
$gw = Get-AzVirtualNetworkGateway -Name $GWName -ResourceGroupName $ResourceGroupName
$connection = New-AzVirtualNetworkGatewayConnection -Name "ERConnection" -ResourceGroupName $ResourceGroupName -Location $Location -VirtualNetworkGateway1 $gw -PeerId $id -ConnectionType ExpressRoute -AuthorizationKey $AuthorizationKey

