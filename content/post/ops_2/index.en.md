---
title: High-Performance Cluster Operations — Software Environment (Modules, MPI, oneAPI)
description: Operations and Maintenance Notes (Part 2)
slug: ops_2
date: 2025-05-11
math: true
image: img/cover2.png
categories:
- 技术文档
tags:
- Technology
- Operations and Maintenance
weight: 4
---

> ⚠️ Please note that the content here was translated by a large language model.

This blog post introduces the commonly used cluster version management software MODULES, as well as two implementations of MPI (UCX+OpenMPI/MPICH), and the installation and configuration of Intel oneAPI. MODULES (latest version released in November 2024) has complex software dependencies and requires modulefiles written in TCL (which can be addressed with generative AI). In the future, there will be opportunities to learn a more user-friendly alternative like spack.

## MODULES (v5.4.0)

![ENVIRONMENT MODULES](img/1.png)

### References

[TCL Official Website](https://www.tcl.tk/)

[MODULES Installation Documentation](https://modules.readthedocs.io/en/latest/INSTALL.html#installation-instructions)

[GCC Official Mirror Site](https://gcc.gnu.org/mirrors.html)

[GCC Build Guide](https://gcc.gnu.org/install/build.html)

---

[[ Module ] Environment Variable Management Tool Modules Installation and Usage - YEUNGCHIE](https://www.cnblogs.com/yeungchie/p/16268954.html)

[module Usage - PKU High-Performance Computing Public Platform User Documentation](https://hpc.pku.edu.cn/ug/guide/module/#:~:text=Module%E4%BD%BF%E7%94%A8)

### Installation Dependencies

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

### Installing MODULES

```bash
sudo curl -LJO https://github.com/cea-hpc/modules/releases/download/v5.4.0/modules-5.4.0.tar.gz
sudo tar xfz modules-5.4.0.tar.gz
sudo ./configure --with-tcl=/usr/local/lib --prefix=/home/Modules --modulefilesdir=/home/modulefiles
sudo make
sudo make install
sudo ln -s /home/Modules/init/profile.sh /etc/profile.d/module.sh
sudo ln -s /home/Modules/init/profile.csh /etc/profile.d/module.csh

source /home/Modules/init/profile.sh  # Recommended to add to /etc/profile, otherwise manual initialization (`source /home/Modules/init/profile.sh`) is needed each time you enter the shell
```

> **Note**: Due to certain special reasons, we have to install MODULES and other software in the `/home` directory.
> `/home/moduledownload/` temporarily stores installation packages for TCL (8.6) and MODULE (5.4.0).
> `/home/Module/` contains the actual Module files, including initialization files (with symbolic links).
> `/home/modulefiles/` stores version files for various software (second-level directory is software name, third-level is version number text).
> `/home/apps/` stores the actual software.

## MPI

### References

[MPICH Official Mirror Site](https://www.mpich.org/static/downloads/)

[OpenMPI v5.0.0](https://download.open-mpi.org/release/open-mpi/v5.0/openmpi-5.0.0.tar.gz)

[UCX Repository](https://github.com/openucx/ucx)

<!-- [ucx release v1.15.0](https://github.com/openucx/ucx/releases/download/v1.15.0/ucx-1.15.0.tar.gz)

[ucx release v1.17.0](https://github.com/openucx/ucx/releases/download/v1.17.0/ucx-1.17.0.tar.gz) -->

---

[Detailed Guide to Building and Installing UCX 1.15.0 and OpenMPI 5.0.0](https://cuterwrite.top/p/openmpi-with-ucx/)

### Installing UCX (optional)

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

### Installing MPICH (v4.2.2)

```bash
tar -xvzf mpich-4.2.2.tar.gz
cd mpich-4.2.2
./configure --prefix=/home/apps/MPICH/4.2.2
make
make install
```

You may encounter an error: `configure: error: UCX installation does not meet minimum version requirement (v1.9.0). Please upgrade your installation, or use --with-ucx=embedded.`

### Installing OpenMPI (v5.0.0)

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

### Writing Modulefile

```TCL
#%Module
set version 4.2.2
set MPI_HOME /home/apps/MPICH/4.2.2
prepend-path PATH "${MPI_HOME}/bin"
prepend-path LD_LIBRARY_PATH "${MPI_HOME}/lib"
prepend-path MANPATH "${MPI_HOME}/share/man"
```

## Intel oneAPI

### References

[Developer Toolkits](https://www.intel.cn/content/www/cn/zh/developer/tools/oneapi/toolkits.html)

[Get the Intel® oneAPI Base Toolkit](https://www.intel.cn/content/www/cn/zh/developer/tools/oneapi/base-toolkit-download.html?packages=oneapi-toolkit&oneapi-toolkit-os=linux)

[Get Intel® oneAPI HPC Toolkit](https://www.intel.cn/content/www/cn/zh/developer/tools/oneapi/hpc-toolkit-download.html?packages=hpc-toolkit&hpc-toolkit-os=linux)

[Intel oneAPI Mirror Site](https://get.hpc.dev/vault/intel/)

### Installing Intel oneAPI (v2025.0 including Base Toolkit and HPC Toolkit)

![Intel oneAPI](img/4.png)

Follow the official offline installation method. Note that when Intel updates oneAPI, the old version interface will be removed, so installing older versions relies on mirror sites and other sources. However, new versions may not be user-friendly; for example, in 2025.0, `mpiicc` still uses `icc` as the compiler, but in 2025.0 (including late 2023 versions and 2024.x), the suite no longer includes `icc`. `icc` was removed in the oneAPI released in the second half of 2023.

```bash
# install base toolkit
wget https://registrationcenter-download.intel.com/akdlm/IRC_NAS/dfc4a434-838c-4450-a6fe-2fa903b75aa7/intel-oneapi-base-toolkit-2025.0.1.46_offline.sh
sudo sh ./intel-oneapi-base-toolkit-2025.0.1.46_offline.sh -a --silent --cli --eula accept
# install HPC toolkit
wget https://registrationcenter-download.intel.com/akdlm/IRC_NAS/b7f71cf2-8157-4393-abae-8cea815509f7/intel-oneapi-hpc-toolkit-2025.0.1.47_offline.sh
sudo sh ./intel-oneapi-hpc-toolkit-2025.0.1.47_offline.sh -a --silent --cli --eula accept
```
