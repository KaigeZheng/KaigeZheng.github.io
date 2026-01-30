---
title: 高性能クラスター運用管理——ソフトウェア環境（Modules、MPI、oneAPI）
description: 運用ノート（その2）
slug: ops_2
date: 2025-05-11
math: true
image: img/cover2.png
categories:
- 技术文档
tags:
- 技術
- 運用管理
weight: 4
---

> ⚠️ご注意ください、ここにある内容は大規模言語モデルによって翻訳されたものです。

本記事では、クラスターでよく使われるバージョン管理ソフトウェアMODULESと、MPIの2つの実装（UCX+OpenMPI/MPICH）、Intel oneAPIのインストールと設定について紹介します。MODULES（最新版は2024年11月リリース）はソフトウェア依存関係が複雑で、modulefileはTCLで記述する必要があります（生成AIを活用可能）。将来的には、より使いやすいspackの学習も検討します。

## MODULES (v5.4.0)

![ENVIRONMENT MODULES](img/1.png)

### 参考資料

[TCL公式サイト](https://www.tcl.tk/)

[MODULESインストールドキュメント](https://modules.readthedocs.io/en/latest/INSTALL.html#installation-instructions)

[GCC公式ミラーサイト](https://gcc.gnu.org/mirrors.html)

[GCCビルドガイド](https://gcc.gnu.org/install/build.html)

---

[[ Module ] 環境変数管理ツール Modulesのインストールと使い方 - YEUNGCHIE](https://www.cnblogs.com/yeungchie/p/16268954.html)

[module使用例 - 北京大学高性能計算校級公共プラットフォームユーザードキュメント](https://hpc.pku.edu.cn/ug/guide/module/#:~:text=Module%E4%BD%BF%E7%94%A8)

### 依存関係のインストール

#### TCL (>=v8.5)

```bash
sudo wget http://prdownloads.sourceforge.net/tcl/tcl8.6.14-src.tar.gz
sudo tar -zxvf tcl8.6.14-src.tar.gz
cd tcl8.6.14/unix
sudo ./configure --prefix=/usr/local
sudo make
sudo make install

sudo whereis tcl
sudo ln /usr/local/bin/tclsh8.6 /usr/bin/tclsh
```

#### GMP

```bash
sudo wget ftp://ftp.gnu.org/gnu/gmp/gmp-5.0.1.tar.bz2
sudo tar -vxf gmp-5.0.1.tar.bz2
cd gmp-5.0.1/
sudo ./configure --prefix=/usr/local/gmp-5.0.1
sudo make
sudo make install
sudo make check
>>> 全30テスト成功...
```

#### MPFR（バグありだが許容範囲）

```bash
sudo wget https://ftp.gnu.org/gnu/mpfr/mpfr-3.1.5.tar.xz
sudo tar -vxf mpfr-3.1.5.tar.xz
cd mpfr-3.1.5/
sudo ./configure --prefix=/usr/local/mpfr-3.1.5 --with-gmp=/usr/local/gmp-5.0.1
sudo make
sudo make install
```

#### MPC

```bash
sudo wget http://www.multiprecision.org/downloads/mpc-0.9.tar.gz
sudo tar -vxf mpc-0.9.tar.gz
cd mpc-0.9/
sudo ./configure --prefix=/usr/local/mpc-0.9 --with-gmp=/usr/local/gmp-5.0.1/ --with-mpfr=/usr/local/mpfr-3.1.5/
sudo make
sudo make install
```

### MODULESのインストール

```bash
sudo curl -LJO https://github.com/cea-hpc/modules/releases/download/v5.4.0/modules-5.4.0.tar.gz
sudo tar xfz modules-5.4.0.tar.gz
sudo ./configure --with-tcl=/usr/local/lib --prefix=/home/Modules --modulefilesdir=/home/modulefiles
sudo make
sudo make install
sudo ln -s /home/Modules/init/profile.sh /etc/profile.d/module.sh
sudo ln -s /home/Modules/init/profile.csh /etc/profile.d/module.csh

source /home/Modules/init/profile.sh  # 推奨：/etc/profileに書き込み、シェル起動時に自動読み込み（`source /home/Modules/init/profile.sh`は手動実行）
```

> **注意**：特別な事情により、MODULESと他のソフトウェアは`/home`ディレクトリにインストールしています。
> `/home/moduledownload/`にTCL（8.6）とMODULE（5.4.0）のインストールパッケージを一時保存。
> `/home/Module/`にModuleの実ファイル群（初期化ファイルのシンボリックリンク含む）。
> `/home/modulefiles/`に各ソフトウェアのバージョンファイル（modulefile）。2階層目はソフト名、3階層目はバージョン番号のテキスト。
> `/home/apps/`に実際のソフトウェア。

## MPI

### 参考資料

[MPICH公式ミラーサイト](https://www.mpich.org/static/downloads/)

[OpenMPI v5.0.0](https://download.open-mpi.org/release/open-mpi/v5.0/openmpi-5.0.0.tar.gz)

[UCXリポジトリ](https://github.com/openucx/ucx)

<!-- [ucxリリース v1.15.0](https://github.com/openucx/ucx/releases/download/v1.15.0/ucx-1.15.0.tar.gz)

[ucxリリース v1.17.0](https://github.com/openucx/ucx/releases/download/v1.17.0/ucx-1.17.0.tar.gz) -->

---

[UCX 1.15.0とOpenMPI 5.0.0のビルド・インストール：詳細ガイド](https://cuterwrite.top/p/openmpi-with-ucx/)

### UCXのインストール（任意）

{{< figure src="img/2.png#center" width=200px" title="Unified Communication X">}}

<!-- ![Unified Communication X](img/2.png?w=300) -->

```bash
wget https://github.com/openucx/ucx/releases/download/v1.15.0/ucx-1.15.0.tar.gz
tar -xvzf ucx-1.15.0.tar.gz
cd ucx-1.15.0
mkdir build && cd build
../configure --prefix=/home/zhengkaige/ucx
make -j N
make install
```

### MPICH (v4.2.2)のインストール

```bash
tar -xvzf mpich-4.2.2.tar.gz
cd mpich-4.2.2
./configure --prefix=/home/apps/MPICH/4.2.2
make
make install
```

エラー例：`configure: error: UCX installation does not meet minimum version requirement (v1.9.0). Please upgrade your installation, or use --with-ucx=embedded.`

### OpenMPI (v5.0.0)のインストール

![OpenMPI](img/3.png)

```bash
wget https://download.open-mpi.org/release/open-mpi/v5.0/openmpi-5.0.0.tar.gz
tar -xzvf openmpi-5.0.0.tar.gz
cd openmpi-5.0.0
mkdir build && cd build
```

`vim ~/.bashrc`

```bash
export PATH=/home/kambri/software/openmpi/5.0.0-ucx-1.15.0/bin:$PATH
export LD_LIBRARY_PATH=/home/kambri/software/openmpi/5.0.0-ucx-1.15.0/lib:$LD_LIBRARY_PATH
```

### Modulefileの作成例

```TCL
#%Module
set version 4.2.2
set MPI_HOME /home/apps/MPICH/4.2.2
prepend-path PATH "${MPI_HOME}/bin"
prepend-path LD_LIBRARY_PATH "${MPI_HOME}/lib"
prepend-path MANPATH "${MPI_HOME}/share/man"
```

## Intel oneAPI

### 参考資料

[Developer Toolkits](https://www.intel.cn/content/www/cn/zh/developer/tools/oneapi/toolkits.html)

[Intel® oneAPI Base Toolkitの入手](https://www.intel.cn/content/www/cn/zh/developer/tools/oneapi/base-toolkit-download.html?packages=oneapi-toolkit&oneapi-toolkit-os=linux)

[Intel® oneAPI HPC Toolkitの入手](https://www.intel.cn/content/www/cn/zh/developer/tools/oneapi/hpc-toolkit-download.html?packages=hpc-toolkit&hpc-toolkit-os=linux)

[Intel oneAPIミラーサイト](https://get.hpc.dev/vault/intel/)

### Intel oneAPIのインストール（2025年版、Base ToolkitとHPC Toolkit含む）

![Intel oneAPI](img/4.png)

公式のオフラインインストール方式に従ってインストールしてください。注意点として、IntelはoneAPIの更新時に古いバージョンのUIを削除するため、旧バージョンのインストールにはミラーサイト等を利用します。ただし、新バージョンは使い勝手が悪く、例えば2025.0の`mpiicc`は依然として`icc`をコンパイラとして使用していますが、2025.0（2023後半や2024.xも含む）には`icc`が含まれていません。`icc`は2023年後半にリリースされたoneAPIから削除済みです。

```bash
# Base Toolkitのインストール
wget https://registrationcenter-download.intel.com/akdlm/IRC_NAS/dfc4a434-838c-4450-a6fe-2fa903b75aa7/intel-oneapi-base-toolkit-2025.0.1.46_offline.sh
sudo sh ./intel-oneapi-base-toolkit-2025.0.1.46_offline.sh -a --silent --cli --eula accept
# HPC Toolkitのインストール
wget https://registrationcenter-download.intel.com/akdlm/IRC_NAS/b7f71cf2-8157-4393-abae-8cea815509f7/intel-oneapi-hpc-toolkit-2025.0.1.47_offline.sh
sudo sh ./intel-oneapi-hpc-toolkit-2025.0.1.47_offline.sh -a --silent --cli --eula accept
```
