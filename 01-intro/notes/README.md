# GCP Environment Setup with Terraform + Cloud-Init

## Description

This repository contains scripts to provision a Google Cloud Platform (GCP) virtual machine using **Terraform**, with automated configuration through **cloud-init**.

The setup replicates the environment demonstrated in the video **"1.2 - Environment Preparation"**.

---

## Setup Instructions

### Step 1: Authenticate with Google Cloud

Ensure you have the **Google Cloud CLI** installed, then run:

```bash
gcloud auth application-default login
```

---

### Step 2: Prepare Configuration Files

1. Copy the following files to your working directory:
   - `main.tf`
   - `cloud-config.yaml`

2. Update the following in the files:
   - Replace placeholder variables as needed
   - Add your **SSH public key** to enable access

---

### Step 3: Initialize and Apply Terraform

Ensure **Terraform** is installed. Then run:

```bash
terraform init
terraform apply
```

> Note: After the VM is created, it may take a few minutes for **cloud-init** to fully configure the environment.

---