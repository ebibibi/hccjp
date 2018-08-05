provider "azurerm" {
    subscription_id = "${var.subscription_id}"
    client_id = "${var.client_id}"
    client_secret = "${var.client_secret}"
    tenant_id = "${var.tenant_id}"
}

variable "subscription_id" {}
variable "client_id" {}
variable "client_secret" {}
variable "tenant_id" {}

variable "resourcename" {
  default = "resourcegroup"
}

variable "location" {
  default = "japaneast"
}

variable "vmname" {
  default = "vmname"
}

variable "vmsize" {
  default = "Standard_D2s_v3"
}

variable "adminusername" {
  default = "admin"
}

variable "adminpassword" {
  default = "P@ssw0rdOfAdmin"
}
