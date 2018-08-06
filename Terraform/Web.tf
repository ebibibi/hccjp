resource "azurerm_resource_group" "webresourcegroup" {
  name     = "HCCJPWeb"
  location = "${var.location}"
}

resource "azurerm_app_service_plan" "appserviceplan" {
  name                = "HCCJPappserviceplan"
  location            = "${azurerm_resource_group.resourcegroup.location}"
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

resource "azurerm_app_service" "hccjpwordpress" {
  name                = "hccjpwordpress"
  location            = "${azurerm_resource_group.webresourcegroup.location}"
  resource_group_name = "${azurerm_resource_group.webresourcegroup.name}"
  app_service_plan_id = "${azurerm_app_service_plan.appserviceplan.id}"

  
  site_config {
    always_on = "true"
    linux_fx_version = "DOCKER|ebibibi/wordpress-cocoon"
  }

  app_settings {
    DOCKER_ENABLE_CI = "true"
    WEBSITE_HTTPLOGGING_RETENTION_DAYS = "7"
    WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"
    WORDPRESS_DB_HOST = "${azurerm_mysql_server.mysqlserver.name}.mysql.database.azure.com"
    WORDPRESS_DB_USER = "${azurerm_mysql_server.mysqlserver.administrator_login}@${var.mysqlname}"
    WORDPRESS_DB_PASSWORD = "${var.mysqladministrator_login_password}"
  }
}

variable mysqlname {}
variable mysqladministrator_login {}
variable mysqladministrator_login_password {}

resource "azurerm_mysql_server" "mysqlserver" {
  name                = "${var.mysqlname}"
  location            = "${azurerm_resource_group.resourcegroup.location}"
  resource_group_name = "${azurerm_resource_group.webresourcegroup.name}"

  sku {
    name     = "B_Gen4_2"
    capacity = 2
    tier     = "Basic"
    family   = "Gen4"
  }

  storage_profile {
    storage_mb            = 51200
    backup_retention_days = 7
    geo_redundant_backup  = "Disabled"
  }

  administrator_login          = "${var.mysqladministrator_login}"
  administrator_login_password = "${var.mysqladministrator_login_password}"
  version                      = "5.7"
  ssl_enforcement              = "Disabled"
}

resource "azurerm_mysql_firewall_rule" "mysqlfirewall" {
  name                = "any"
  resource_group_name = "${azurerm_resource_group.webresourcegroup.name}"
  server_name         = "${azurerm_mysql_server.mysqlserver.name}"
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "255.255.255.255"
}

resource "azurerm_mysql_database" "mysqldatabase" {
  name                = "wordpress"
  resource_group_name = "${azurerm_resource_group.webresourcegroup.name}"
  server_name         = "${azurerm_mysql_server.mysqlserver.name}"
  charset             = "utf8"
  collation           = "utf8_unicode_ci"
}
