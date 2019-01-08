Param(
    [parameter(mandatory=$true)]
    [string]$Owner,
    [string]$OfferName = "pocoffer",
    [string]$ResourceGroupName = "offers"
)

$SubscriptionName = "subscription for $Owner"
$PoCOffer = Get-AzsManagedOffer -Name $OfferName -ResourceGroupName $ResourceGroupName
New-AzsUserSubscription -Owner $Owner -OfferId $PoCOffer.Id -DisplayName $SubscriptionName

