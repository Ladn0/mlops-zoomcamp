terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.35.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_compute_instance" "mlopsvm" {

  # Required
  boot_disk {
    auto_delete = true
    device_name = "mlopsdisk"

    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/ubuntu-2404-noble-amd64-v20250502a"
      size  = 30
      type  = "pd-balanced"
    }

    mode = "READ_WRITE"
  }

  network_interface {
    access_config {
      network_tier = "PREMIUM"
    }

    queue_count = 0
    stack_type  = "IPV4_ONLY"
    subnetwork  = var.subnetwork
  }

  machine_type = "e2-standard-4"

  name = "mlopsvm"

  zone = var.zone


  # Optional
  deletion_protection = false

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
    preemptible         = false
    provisioning_model  = "STANDARD"
  }

  shielded_instance_config {
    enable_integrity_monitoring = true
    enable_secure_boot          = false
    enable_vtpm                 = true
  }

  # Cloud init 
  metadata = {
    user-data = file("cloud-config.yaml")
  }

}
