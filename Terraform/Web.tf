resource "azurerm_resource_group" "webresourcegroup" {
        name = "HCCJPWeb"
        location = "${var.location}"
}