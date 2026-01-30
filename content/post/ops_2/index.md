---
title: 高性能集群运维——软件环境（Modules、MPI、oneAPI）
description: 运维笔记（二）
slug: ops_2
date: 2025-05-11
math: true
image: img/cover2.png
categories:
    - 技术文档
tags:
    - 技术
    - 运维
weight: 4
---

本篇博文介绍集群常用版本管理软件MODULES，以及MPI的两种实现（UCX+OpenMPI/MPICH）、Intel oneAPI的安装配置。MODULES（最新版的发行版发布自24年11月）的软件依赖繁琐且modulefile需要用TCL写（可以用生成式AI解决），未来有机会学习一下更易用的spack。

## MODULES (v5.4.0)

![ENVIRONMENT MODULES](img/1.png)

### 参考

[TCL官网](https://www.tcl.tk/)

[MODULES安装文档](https://modules.readthedocs.io/en/latest/INSTALL.html#installation-instructions)

[GCC官方镜像站](https://gcc.gnu.org/mirrors.html)

[GCC构建指南](https://gcc.gnu.org/install/build.html)

---

[[ Module ] 环境变量管理工具 Modules 安装和使用 - YEUNGCHIE](https://www.cnblogs.com/yeungchie/p/16268954.html)

[module使用 - 北京大学高性能计算校级公共平台用户文档](https://hpc.pku.edu.cn/ug/guide/module/#:~:text=Module%E4%BD%BF%E7%94%A8)

### 安装依赖

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
>>> All 30 tests passed...
```

#### MPFR (buggy but acceptable)

```bash
sudo wget https://ftp.gnu.org/gnu/mpfr/mpfr-3.1.5.tar.xz
sudo tar -vxf mpfr-3.1.5.tar.gz
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

### 安装MODULES

```bash
sudo curl -LJO https://github.com/cea-hpc/modules/releases/download/v5.4.0/modules-5.4.0.tar.gz
sudo tar xfz modules-5.4.0.tar.gz
sudo ./configure --with-tcl=/usr/local/lib --prefix=/home/Modules --modulefilesdir=/home/modulefiles
sudo make
sudo make install
sudo ln -s /home/Modules/init/profile.sh /etc/profile.d/module.sh
sudo ln -s /home/Modules/init/profile.csh /etc/profile.d/module.csh

source /home/Modules/init/profile.sh  # 建议写入/etc/profile，否则每次进入shell需要手动初始化(`source /home/Modules/init/profile.sh`)
```

> **Note**因为某些特殊的原因，我们不得不将MODULES和其他软件安装在`/home`目录下
> `/home/moduledownload/`暂时存放TCL（8.6）和MODULE（5.4.0）的安装包等
> `/home/Module/`存放Module的实际文件，内含初始化文件（已做软链接）
> `/home/modulefiles/`存放各个软件的版本文件（modulefile），第二级文件为软件名，第三级文件为版本号文本
> `/home/apps/`存放实际软件

## MPI

### 参考

[MPICH官方镜像站](https://www.mpich.org/static/downloads/)

[OpenMPI v5.0.0](https://download.open-mpi.org/release/open-mpi/v5.0/openmpi-5.0.0.tar.gz)

[UCX仓库](https://github.com/openucx/ucx)

<!-- [ucx release v1.15.0](https://github.com/openucx/ucx/releases/download/v1.15.0/ucx-1.15.0.tar.gz)

[ucx release v1.17.0](https://github.com/openucx/ucx/releases/download/v1.17.0/ucx-1.17.0.tar.gz) -->

---

[编译安装 UCX 1.15.0 与 OpenMPI 5.0.0：详尽指南](https://cuterwrite.top/p/openmpi-with-ucx/)

### 安装UCX (optional)

{{< figure src="img/2.png#center" width=200px" title="Unified Communication X">}}

<!-- ![Unified Communication X](img/2.png?w=300) -->

```bash
wget https://github.com/openucx/ucx/releases/download/v1.15.0/ucx-1.15.0.tar.gz
tar -xvzf ucx-1.15.0.tar.gz
cd ucx-1.15.0
mkdir build & cd build
../configure --prefix=/home/zhengkaige/ucx
make -j N
make install
```

### 安装MPICH (v4.2.2)

```bash
tar -xvzf mpich-4.2.2.tar.gz
cd mpich-4.2.2
./configure --prefix=/home/apps/MPICH/4.2.2
make
make install
```

可能遇到报错：`configure: error: UCX installation does not meet minimum version requirement (v1.9.0). Please upgrade your installation, or use --with-ucx=embedded.`

### 安装OpenMPI (v5.0.0)

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

### 编写Modulefile

```TCL
#%Module
set version 4.2.2
set MPI_HOME /home/apps/MPICH/4.2.2
prepend-path PATH "${MPI_HOME}/bin"
prepend-path LD_LIBRARY_PATH "${MPI_HOME}/lib"
prepend-path MANPATH "${MPI_HOME}/share/man"
```

## Intel oneAPI

### 参考

[Developer Toolkits](https://www.intel.cn/content/www/cn/zh/developer/tools/oneapi/toolkits.html)

[Get the Intel® oneAPI Base Toolkit](https://www.intel.cn/content/www/cn/zh/developer/tools/oneapi/base-toolkit-download.html?packages=oneapi-toolkit&oneapi-toolkit-os=linux&oneapi-lin=offline)

[Get Intel® oneAPI HPC Toolkit](https://www.intel.cn/content/www/cn/zh/developer/tools/oneapi/hpc-toolkit-download.html?packages=hpc-toolkit&hpc-toolkit-os=linux&hpc-toolkit-lin=offline)

[Intel oneAPI镜像站](https://get.hpc.dev/vault/intel/)

### 安装Intel oneAPI(v2025.0 including Base Toolkit and HPC Toolkit)

![Intel oneAPI](img/4.png)

按照官方的offline installation方式下载安装即可。需要注意的是Intel更新oneAPI时会移除老版本界面，因此安装老版本时需要靠镜像站等途径。但新版本又不好用，如2025.0的`mpiicc`仍然使用`icc`作为compiler，但是2025.0（包括2023后期版本和2024.x）的套件里都已不包含`icc`了。`icc`已在2023下半年发布的oneAPI中被移除。

```bash
# install base toolkit
wget https://registrationcenter-download.intel.com/akdlm/IRC_NAS/dfc4a434-838c-4450-a6fe-2fa903b75aa7/intel-oneapi-base-toolkit-2025.0.1.46_offline.sh
sudo sh ./intel-oneapi-base-toolkit-2025.0.1.46_offline.sh -a --silent --cli --eula accept
# install HPC toolkit
wget https://registrationcenter-download.intel.com/akdlm/IRC_NAS/b7f71cf2-8157-4393-abae-8cea815509f7/intel-oneapi-hpc-toolkit-2025.0.1.47_offline.sh
sudo sh ./intel-oneapi-hpc-toolkit-2025.0.1.47_offline.sh -a --silent --cli --eula accept
```