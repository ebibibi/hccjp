resource "azurerm_resource_group" "exresourcegroup" {
  name     = "ExpressRoute"
  location = "Japan East"
}

resource "azurerm_express_route_circuit" "expressroute" {
  name                  = "hccjp_expressroute"
  resource_group_name   = "${azurerm_resource_group.exresourcegroup.name}"
  location              = "${azurerm_resource_group.exresourcegroup.location}"
  service_provider_name = "IIJ"
  peering_location      = "Tokyo"
  bandwidth_in_mbps     = 50

  sku {
    tier   = "Standard"
    family = "MeteredData"
  }
}
