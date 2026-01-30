---
title: 高性能クラスター運用管理——セットアップ
description: 運用ノート（1）
slug: ops
date: 2025-04-23
math: true
image: img/cover.png
categories:
- 技术文档
tags:
- 技術
- 運用管理
weight: 3
---

> ⚠️ご注意ください、ここにある内容は大規模言語モデルによって翻訳されたものです。

この期間、機房とのやり取りが多く、三江源データ分析センターに新しい購入機器を設置するエンジニアや学院の運用担当の先生方と連携してきました。そこで、高性能クラスター構築の経験をまとめます。

## ハードウェア

### 組み立て

新たに購入した整備済みサーバーには、ハードディスク、メモリ、ネットワークカード（Ethernet）、RAIDカードが揃っています。起動時には、メイン電源と予備電源の両方が点灯していることを必ず確認してください。構成は、Intelのデュアルソケットマシン2台とAMDのデュアルソケットマシン2台です。RDMAネットワークカードは別途調達し、Mellanox MT28908（ConnectX-6）を使用しています。高性能計算センターからNVIDIA A800 80GB PCIEカード8枚を借用し、トポロジーは4台のマシンに8枚のカードを配置する予定です。

|         サーバー         |               CPU               |       メモリ       |                ハードディスク                |
|:----------------------:|:-------------------------------:|:------------------:|:-------------------------------------------:|
| H3C UniServer R4900 G6 | Intel(R) Xeon(R) GOLD 6542Y(250w)×2     | 32G DDR5 5600×8    | 960G SSD×2 + 4TB SATA×3 + RAID PM8204-2G |
| H3C UniServer R4950 G6 | AMD EPYC 9654 96コアプロセッサ(360w)×2 | 32G DDR5 4800×8    | 960G SSD×2 + 4TB SATA×3 + RAID PM8204-2G |


![サーバー内部](img/1.jpg)

### 起動ディスクの作成

ブート可能なISOイメージ、書き込みソフト（[Rufus](https://rufus.ie/en/)または[UltraISO](https://ultraiso.net/)）、およびUSBメモリ（できればUSB3.0推奨）を準備します。ここではサーバー側の`Ubuntu Server 22.04.5 LTS`（長期サポート版、2027年4月までサポート）を選択し、[Ubuntu公式サイト](https://cn.ubuntu.com/download)からブート可能なISOファイルを取得します。

![ISOファイル](img/2.png)

次に、書き込みソフトを使ってハードディスクにイメージを書き込みます。UltraISOでは書き込み方式を`USB-HDD+`に設定し、Rufusではターゲットシステムタイプを`BIOSまたはUEFI`に設定します。必要に応じてファイルシステムやその他の設定を調整してください。フォーマット後、システムイメージを書き込み（約2〜3分）ます。

![Rufusで起動ディスク作成](img/3.png) ![UltraISOで起動ディスク作成](img/4.png)

## ソフトウェア

### ネットワーク設定

通常、システムインストール時には設定しません。インストール完了後に`ip link show`コマンドでネットワークインターフェース名を確認します。次に`vim /etc/netplan/50-cloud-init.yaml`を編集し、以下のように設定します。

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

### rootパスワードの設定

```bash
su root
passwd root
```

### Linuxカーネルの自動更新を無効化

無効にしないと、`apt update`後にサービスの再起動や更新を促す通知が出続けます。`/etc/apt/apt.conf.d/`内の`10periodic`と`20auto-upgrades`のパラメータを`0`に変更します。

`sudo vim /etc/apt/apt.conf.d/10periodic`

内容を以下に更新：

```bash
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
```

`sudo vim /etc/apt/apt.conf.d/20auto-upgrades`

内容を以下に更新：

```bash
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Unattended-Upgrade "0";
```

### リバースプロキシ設定

計算ノードはインターネットに接続しないため、ローカルを踏み台としてリバースプロキシを設定します。

`Users/username/.ssh/config`に以下を追加：

```bash
Host <hostname>
  HostName <IP>
  Port <port>
  User <username>
  RemoteForward <Port1> 127.0.0.1:<Port2>
```

最近学んだ方法として、`.ssh/config`内で`ProxyJump`を設定し、シームレスに踏み台接続を行うことも可能です。パスワード不要にするには、接続先ホストの`~/.ssh/authorized_keys`に**ローカルの公開鍵**を登録してください。

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

### 事前準備のポイント

```bash
# Linuxの自動休眠を無効化
echo "\$nrconf{kernelhints} = 0;" >> /etc/needrestart/needrestart.conf
echo "\$nrconf{restart} = 'l';" >> /etc/needrestart/needrestart.conf
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
# aptとapt-getの更新
apt update
apt upgrade
apt-get update
apt-get upgrade
# 必要なパッケージのインストール
apt install git wget vim curl htop net-tools pciutils build-essential 
```

### パーティション設定

ディスクが認識されない場合、システムインストール時にエラー`block probing did not discover any disks`が出ることがあります。ハードディスクやRAIDカードの点灯状態を確認してください。

```bash
lsblk # 新しいディスクのデバイス名を確認（例：/dev/sdX）
sudo pvcreate /dev/sdb /dev/sdc /dev/sdd # 物理ボリュームの作成
sudo vgcreate vg_home /dev/sdb /dev/sdc /dev/sdd # ボリュームグループの作成
vgdisplay # ボリュームグループ情報を確認
sudo lvcreate -l 100%FREE -n lv_home vg_home # 全容量を使った論理ボリューム作成
sudo mkfs.ext4 /dev/vg_home/lv_home # ext4ファイルシステムでフォーマット
sudo mount /dev/vg_home/lv_home /home # /homeにマウント
# 自動マウント設定
sudo blkid /dev/vg_home/lv_home # UUIDを取得
sudo vim /etc/fstab
>>> UUID=<UUID> /home ext4 defaults 0 2
sudo mount -a
df -a # 正常にマウントされたか確認
```

### NFS共有ファイルシステム

```bash
sudo apt install nfs-kernel-server nfs-common rdma-core # 全ノードで実行
```

#### NFSサーバー設定

```bash
sudo mkdir -p /home
sudo chmod 777 /home
sudo vim /etc/exports
>>> /home *(rw,sync,no_root_squash) 
sudo vim /etc/nfs.conf # RDMAを有効化
>>> [nfsd]
>>> rdma=y
sudo systemctl restart nfs-kernel-server
sudo systemctl enable nfs-kernel-server
```

#### クライアント設定

```bash
sudo mount -o rdma,vers=4.2 <server_ip>:/home /home
df -h | grep /home # マウント成功を確認
sudo vim /etc/fstab
>>> <server_ip>:/home /home nfs4 rdma,vers=4.2 0 0
```

#### RDMA伝送の検証

```bash
mount | grep /home
cat /proc/fs/nfsfs/servers # transport列がrdmaになっているか確認
```

### InfiniBandドライバ

ドライバのダウンロード：[NVIDIA InfiniBand Software | NVIDIA | NVIDIA Developer](https://developer.nvidia.com/networking/infiniband-software)

MLNX_OFED：[Linux InfiniBand Drivers](https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/)

古いバージョンのIBを使用する場合は、リリースノートでサポート状況を確認してください。

IBデバイスの確認：

```bash
lspci | grep -i mell
```

IBのopensmサービスを起動：

```bash
# 未インストールの場合
sudo apt update && sudo apt upgrade -y
sudo apt install opensm infiniband-diags ibutils perftest -y
sudo systemctl start opensm
systemctl status opensm
sudo systemctl enable opensm # 自動起動設定
```

IBデバイスの認識状況を確認：

```bash
ibv_devinfo
ibstat
```

サーバーとクライアントのIB帯域をテスト：

```bash
ibv_devices # デバイス名を確認（例：mlx5_0）
ib_read_bw -a -d <device_name> --report_gbits # サーバー側
ib_read_bw -a -F <ip_addr> -d <device_name> --report_gbits # クライアント側（-aは全メッセージサイズ、-Fはサーバーへの接続を強制、--report_gbitsはGbps単位で表示）
```

![サーバー](img/5.png) ![クライアント](img/6.png)

MTU（最大伝送単位）の設定：

```bash
ifconfig | grep ib # IBインターフェースを確認
ifconfig ib0 mtu 65520 # 両方のマシンで同じMTU値に設定
```

> 簡単なテスト：`ibping`または`ibping <ip_addr>`を実行

### CUDA

#### Nouveauドライバの無効化/アンインストール（必要に応じて）

```bash
sudo vim /etc/modprobe.d/blacklist.conf
```

最後に以下を追加：

```bash
blacklist nouveau
options nouveau modeset=0
```

initramfsを再構築し、サーバーを再起動して反映させます。

```bash
sudo update-initramfs -u
sudo reboot
```

`lsmod | grep nouveau`で確認し、出力がなければ無効化成功です。

#### ドライバのインストール

GPUモデルを確認：

```bash
lspci | grep -i nvidia
```

ドライバのダウンロード：[NVIDIA Driver](https://www.nvidia.com/en-us/drivers/)

> A800/V100用CUDA12.6ドライバ例：
> [Data Center Driver for Linux x64 560.35.03 | Linux 64-bit | NVIDIA](https://www.nvidia.com/en-us/drivers/details/231430/)

ドライバのアンインストール：

```bash
sudo /usr/bin/nvidia-uninstall
```

CUDAのインストール：[CUDA Toolkit 12.6 Update 3](https://developer.nvidia.com/cuda-downloads)

CUDA Toolkitのアーカイブ：[CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive)

`NVCC`はCUDA Toolkitに含まれるため、[公式サイト](https://developer.nvidia.com/cuda-downloads)から対応バージョンの`runfile`をダウンロードし、以下のようにインストールします。

例：CUDA Toolkit 12.2の場合

```bash
wget https://developer.download.nvidia.com/compute/cuda/12.9.1/local_installers/cuda_12.9.1_575.57.08_linux.run
sudo sh cuda_12.9.1_575.57.08_linux.run
```

ドライバの再インストールは不要です。インストール後、環境変数を設定します。

```bash
echo 'export PATH=/usr/local/cuda-12.2/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

`/usr/local/cuda`をデフォルトパスとして使いたい場合は、シンボリックリンクを作成します。

```bash
sudo ln -s /usr/local/cuda-12.2 /usr/local/cuda
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```
