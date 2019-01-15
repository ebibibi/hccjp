Param(
    [parameter(mandatory=$true)]
    $UserName
)

Connect-AzAccount -Subscription 44bc783b-d8d7-4a07-8af1-83cc11310ad3 #HCCJP 

$circuit = Get-AzExpressRouteCircuit -Name "hccjp_expressroute" -ResourceGroupName "ExpressRoute"
Add-AzExpressRouteCircuitAuthorization -ExpressRouteCircuit $circuit -Name $UserName
Set-AzExpressRouteCircuit -ExpressRouteCircuit $circuit

$circuit = Get-AzExpressRouteCircuit -Name "hccjp_expressroute" -ResourceGroupName "ExpressRoute"
$auth = Get-AzExpressRouteCircuitAuthorization -ExpressRouteCircuit $circuit -Name $UserName

Write-Host "AuthorizationKey:"
$auth.AuthorizationKey
