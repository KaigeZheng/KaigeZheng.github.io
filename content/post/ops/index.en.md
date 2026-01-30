---
title: High-Performance Cluster Operations and Maintenance — Installation
description: Operations and Maintenance Notes (1)
slug: ops
date: 2025-04-23
math: true
image: img/cover.png
categories:
- 技术文档
tags:
- Technology
- Operations and Maintenance
weight: 3
---

> ⚠️ Please note that the content here was translated by a large language model.

Recently, I have been dealing more with the machine room, responsible for coordinating engineers who installed newly purchased machines for the Sanjiangyuan Data Analysis Center and the college's operations teachers. So, I am summarizing the experience of building a high-performance cluster during this period.

## Hardware

### Assembly

The newly purchased complete servers come with hard drives, memory sticks, Ethernet network cards, and RAID cards already installed. Be sure to ensure that both the main power and backup power are lit during startup. The machine configurations are as follows: two machines with dual Intel processors and two with dual AMD processors. The RDMA network cards were purchased separately: Mellanox MT28908 (ConnectX-6). We borrowed 8 NVIDIA A800 80GB PCIe cards from the High-Performance Computing Center, with an expected topology of four machines and eight cards.

|         Server         |               CPU               |       Memory       |                Hard Disk                |
|:----------------------:|:-------------------------------:|:------------------:|:---------------------------------------:|
| H3C UniServer R4900 G6 | Intel(R) Xeon(R) GOLD 6542Y(250w)×2     | 32G DDR5 5600×8    | 960G SSD×2 + 4TB SATA×3 + RAID PM8204-2G |
| H3C UniServer R4950 G6 | AMD EPYC 9654 96-Core Processor(360w)×2 | 32G DDR5 4800×8    | 960G SSD×2 + 4TB SATA×3 + RAID PM8204-2G |


![Server Interior](img/1.jpg)

### Creating Bootable USB Drive

Prepare a bootable ISO, burning software ([Rufus](https://rufus.ie/en/) or [UltraISO](https://ultraiso.net/)), and a USB drive (preferably USB 3.0). Here, we choose the server-side `Ubuntu Server 22.04.5 LTS` (the previous long-term support version of Ubuntu Server, supported until April 2027). Download the bootable ISO from the [Ubuntu official website](https://cn.ubuntu.com/download).

![ISO File](img/2.png)

Next, use the burning software to write the image to the disk. For UltraISO, select the write mode as `USB-HDD+`; for Rufus, set the target system type to `BIOS or UEFI`. Configure the filesystem and other settings as needed. After formatting the USB drive, write the system image (about 2-3 minutes).

![Rufus Bootable USB](img/3.png) ![UltraISO Bootable USB](img/4.png)

## Software

### Network Configuration

Usually, during system installation, network configuration is not set initially. After installation, check the network interface names with `ip link show`. Then, edit `/etc/netplan/50-cloud-init.yaml` as follows:

```yaml
# ...
network:
    ethernets:
        ens16f0:
            addresses:
            - <A.B.C.D>/24
            nameservers:
                addresses: []
                search: []
            routes:
            -   to: default
                via: <A.B.C.D>
    version: 2
```

### Setting the root password

```bash
su root
passwd root
```

### Disabling Linux Kernel Automatic Updates

If not disabled, after each `apt update`, it will prompt whether to restart services and update. To prevent this, modify the parameters in `/etc/apt/apt.conf.d/10periodic` and `/etc/apt/apt.conf.d/20auto-upgrades` to `0`.

`sudo vim /etc/apt/apt.conf.d/10periodic`

Update to:

```bash
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
```

`sudo vim /etc/apt/apt.conf.d/20auto-upgrades`

Update to:

```bash
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Unattended-Upgrade "0";
```

### Reverse Proxy

Since the compute nodes are not connected to the internet, use the local machine as a jump host for reverse proxy.

Modify `Users/username/.ssh/config`:

```bash
Host <hostname>
  HostName <IP>
  Port <port>
  User <username>
  RemoteForward <Port1> 127.0.0.1:<Port2>
```

Additionally, recently learned that in `.ssh/config`, you can configure `ProxyJump` for seamless jump connections. Note that for passwordless login, the public key must be added to the destination host's `~/.ssh/authorized_keys`.

```bash
Host <hostname>
  HostName <IP>
  Port <port>
  User <username>
  RemoteForward <Port1> 127.0.0.1:<Port2>

Host <destination>
  HostName <IP>
  Port <port>
  User <username>
  ProxyJump <hostname>
  RemoteForward <Port1> 127.0.0.1:<Port2>
```

### Useful Preparations

```bash
# Disable Linux automatic sleep
echo "\$nrconf{kernelhints} = 0;" >> /etc/needrestart/needrestart.conf
echo "\$nrconf{restart} = 'l';" >> /etc/needrestart/needrestart.conf
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
# Update apt and apt-get
apt update
apt upgrade
apt-get update
apt-get upgrade
# Install necessary components
apt install git wget vim curl htop net-tools pciutils build-essential 
```

### Disk Partitioning

If disks are not recognized, errors like `block probing did not discover any disks` may occur during system installation. Check if the disks and RAID cards are lit.

```bash
lsblk # Confirm new disk device names (e.g., /dev/sdX)
sudo pvcreate /dev/sdb /dev/sdc /dev/sdd # Create physical volumes
sudo vgcreate vg_home /dev/sdb /dev/sdc /dev/sdd # Create volume group
vgdisplay # Check volume group info
sudo lvcreate -l 100%FREE -n lv_home vg_home # Create logical volume using all space
sudo mkfs.ext4 /dev/vg_home/lv_home # Format logical volume as ext4
sudo mount /dev/vg_home/lv_home /home # Mount to /home
# Auto-mount on boot
sudo blkid /dev/vg_home/lv_home # Get UUID
sudo vim /etc/fstab
>>> UUID=<UUID> /home ext4 defaults 0 2
sudo mount -a
df -a # Verify
```

### NFS Shared Filesystem

```bash
sudo apt install nfs-kernel-server nfs-common rdma-core # All nodes execute
```

#### NFS Server Node

```bash
sudo mkdir -p /home
sudo chmod 777 /home
sudo vim /etc/exports
>>> /home *(rw,sync,no_root_squash) 
sudo vim /etc/nfs.conf # Enable RDMA
>>> [nfsd]
>>> rdma=y
sudo systemctl restart nfs-kernel-server
sudo systemctl enable nfs-kernel-server
```

#### Client Nodes

```bash
sudo mount -o rdma,vers=4.2 <server_ip>:/home /home
df -h | grep /home # Check if mounted successfully
sudo vim /etc/fstab # Set auto-mount at startup
>>> <server_ip>:/home /home nfs4 rdma,vers=4.2 0 0
```

Verify RDMA transfer:

```bash
mount | grep /home
cat /proc/fs/nfsfs/servers # Check if transport column is rdma
```

### InfiniBand Driver

Download drivers: [NVIDIA InfiniBand Software | NVIDIA | NVIDIA Developer](https://developer.nvidia.com/networking/infiniband-software)

MLNX_OFED: [Linux InfiniBand Drivers](https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/)

For older IB versions, be sure to check the Release Notes for support.

Check IB devices:

```bash
lspci | grep -i mell
```

Start IB's opensm service:

```bash
# If not installed
sudo apt update && sudo apt upgrade -y
sudo apt install opensm infiniband-diags ibutils perftest -y
sudo systemctl start opensm
systemctl status opensm
sudo systemctl enable opensm # Auto-start on boot
```

Verify IB device recognition:

```bash
ibv_devinfo
ibstat
```

Test server and client IB bandwidth:

```bash
ibv_devices # Query device name, e.g., mlx5_0
ib_read_bw -a -d <device_name> --report_gbits # Server
ib_read_bw -a -F <ip_addr> -d <device_name> --report_gbits # Client (-a tests all message sizes, -F forces connection to server (server must be started first), --report_gbits shows bandwidth in Gbps)
```

![Server](img/5.png) ![Client](img/6.png)

Set IB MTU (Maximum Transmission Unit):

```bash
ifconfig | grep ib # Query
ifconfig ib0 mtu 65520 # Ensure both machines' IB interfaces have the same MTU
```

> Simple test: `ibping` and `ibping <ip_addr>`

### CUDA

#### Disable/Uninstall Nouveau Driver (Optional)

```bash
sudo vim /etc/modprobe.d/blacklist.conf
```

Add the following lines at the end:

```bash
blacklist nouveau
options nouveau modeset=0
```

Rebuild initramfs and reboot to apply:

```
sudo update-initramfs -u
sudo reboot
```

Verify with `lsmod | grep nouveau`. If no output, disabling was successful.

#### Install Driver

Check GPU model: `lspci | grep -i nvidia`

Download driver: [NVIDIA Driver](https://www.nvidia.com/en-us/drivers/)

> For A800/V100 with CUDA12.6:
> [Data Center Driver for Linux x64 560.35.03 | Linux 64-bit | NVIDIA](https://www.nvidia.com/en-us/drivers/details/231430/)

#### Uninstall Driver

```bash
sudo /usr/bin/nvidia-uninstall
```

#### Install CUDA

Download CUDA: [CUDA Toolkit 12.6 Update 3](https://developer.nvidia.com/cuda-downloads)

CUDA Toolkit archive: [CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive)

`NVCC` requires the full CUDA toolkit. Download the appropriate version from the [official site](https://developer.nvidia.com/cuda-downloads) (preferably via runfile/local). Use commands like `wget` and `sudo sh`:

```shell
# Example for CUDA Toolkit 12.2
wget https://developer.download.nvidia.com/compute/cuda/12.9.1/local_installers/cuda_12.9.1_575.57.08_linux.run
sudo sh cuda_12.9.1_575.57.08_linux.run
```

No need to reinstall the driver. After installation, add environment variables:

```shell
echo 'export PATH=/usr/local/cuda-12.2/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

To access `/usr/local/cuda` by default, create a symlink:

```bash
sudo ln -s /usr/local/cuda-12.2 /usr/local/cuda
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```
