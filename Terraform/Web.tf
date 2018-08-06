resource "azurerm_resource_group" "webresourcegroup" {
  name     = "HCCJPWeb"
  location = "${var.location}"
}

resource "azurerm_app_service_plan" "appserviceplan" {
  name                = "HCCJPappserviceplan"
  location            = "${azurerm_resource_group.vmresourcegroup.location}"
  resource_group_name = "${azurerm_resource_group.webresourcegroup.name}"
  kind                = "linux"

  sku {
    tier     = "Basic"
    size     = "B1"
    capacity = "1"
  }

  properties {
    reserved         = "true"
    per_site_scaling = "false"
  }
}

variable mysqlname {}
variable mysqladministrator_login {}
variable mysqladministrator_login_password {}

resource "azurerm_mysql_server" "mysqlserver" {
  name                = "${var.mysqlname}"
  location            = "${azurerm_resource_group.vmresourcegroup.location}"
  resource_group_name = "${azurerm_resource_group.webresourcegroup.name}"

  sku {
    name = "B_Gen4_2"
    capacity = 2
    tier = "Basic"
    family = "Gen4"
  }

  storage_profile {
    storage_mb = 51200
    backup_retention_days = 7
    geo_redundant_backup = "Disabled"
  }

  administrator_login = "${var.mysqladministrator_login}"
  administrator_login_password = "${var.mysqladministrator_login_password}"
  version = "5.7"
  ssl_enforcement = "Enabled"
}

resource "azurerm_mysql_database" "mysqldatabase" {
  name                = "wordpress"
  resource_group_name = "${azurerm_resource_group.webresourcegroup.name}"
  server_name         = "${azurerm_mysql_server.mysqlserver.name}"
  charset             = "utf8"
  collation           = "utf8_unicode_ci"
}