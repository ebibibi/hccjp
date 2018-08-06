resource "azurerm_resource_group" "webresourcegroup" {
        name = "HCCJPWeb"
        location = "${var.location}"
}

resource "azurerm_app_service_plan" "appserviceplan" {
  name                = "HCCJPappserviceplan"
  location            = "${var.location}"
  resource_group_name = "${azurerm_resource_group.webresourcegroup.name}"
  kind                = "linux"
  sku {
      tier            = "Standard"
      size            = "B1"
      capacity        = "1"
  }
  
  properties {
    reserved = "true"
    per_site_scaling = "false"
  }


}