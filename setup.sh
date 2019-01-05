#!/bin/bash

check_and_install() {
	HOW=$1
	PKGNAME=$2
	ALTAPTNAME=$3

	echo -n "* Looking for ${PKGNAME}: "
	if [ $HOW == "which" ]; then
		which "${PKGNAME}" > /dev/null
	elif [[ $HOW == "pkgcfg" || $HOW == "pkg-config" ]]; then
		pkg-config --exists "${PKGNAME}" > /dev/null
	elif [[ $HOW == "apt" || $HOW == "apt-list" ]]; then
		apt list --installed 2> /dev/null | grep "${PKGNAME}" > /dev/null
	fi

	if [ $? == 1 ]; then
		echo "NOT FOUND"
		_N=$ALTAPTNAME
		if [ -z "$_N" ]; then
			_N=$PKGNAME
		fi
		echo "* Trying to install ${_N}..."
		sudo apt -y install ${_N} > ${_N}_apt-install.stdout 2> ${_N}_apt-install.stderr
	else
		echo "found"
	fi
}

link_local_py_lib() {
	LIBDIR=$1

	echo "* Linking local Python library '${LIBDIR}'"
	if [ ! -L "env/lib/python2.7/site-packages/${LIBDIR}" ]; then
		pushd "env/lib/python2.7/site-packages/" > /dev/null
		ln -s "../../../../${LIBDIR}" 2> /dev/null > /dev/null
		popd > /dev/null
	fi
}

build_embedded_sps() {
	echo -n "* Fetching embedded-sps submodule: "
	git submodule init >> git-setup.stdout 2>> git-setup.stderr
	git submodule update --recursive >> git-setup.stdout 2>> git-setup.stderr
	pushd embedded-sps > /dev/null
	git submodule init >> git-setup.stdout 2>> git-setup.stderr
	git submodule update --recursive >> git-setup.stdout 2>> git-setup.stderr
	echo "done"
	echo -n "* Building embedded-sps submodule: "
	make release > make.release.stdout 2> make.release.stderr
	pushd release/sps30-i2c > /dev/null
	pushd hw_i2c > /dev/null
	mv sensirion_hw_i2c_implementation.c sensirion_hw_i2c_implementation.c.orig
	ln -s sample-implementations/linux_user_space/sensirion_hw_i2c_implementation.c
	popd > /dev/null
	make > make.stdout 2> make.stderr
	if [ -f libsps30.so ]; then
		numSyms=`nm libsps30.so | grep -i sps | wc -l`
		cp libsps30.so ../../../lib/rpjios/devices/
		echo "success (${numSyms})"
	else
		echo  "failure!"
	fi
	popd > /dev/null
	popd > /dev/null
}


cat /etc/os-release | perl -ne "exit(1), if (/ID_LIKE=debian/)"
if [ $? != 1 ]; then
	echo "** Looks like you're not on a Debian-like system, and I need 'apt'. Sorry."
	exit -1
fi

IS_RPI=1
REQ_FILE=requirements.txt

cat /etc/os-release | perl -ne "exit(1), if (/ID=raspbian/)"
if [ $? != 1 ]; then
	echo "*** Non-RPi platform detected: omitting unneeded modules."
	IS_RPI=0
	REQ_FILE=requirements-nonRPi.txt
else
	echo "*** RPi platform detected: building sensor drivers and including hardware interface modules."
fi

echo

check_and_install "which" "virtualenv"
check_and_install "apt" "redis-server"
check_and_install "which" "zip"
check_and_install "apt" "python-dev"
check_and_install "apt" "libjpeg9-dev"

if [ ${IS_RPI} == 1 ]; then
	check_and_install "apt" "python-smbus"
	build_embedded_sps
fi

if [ ! -d "./env" ]; then
	echo -n "* Initializing virtualenv: "
	virtualenv --system-site-packages --prompt="(rpjios venv) " ./env > virtualenv-init.stdout 2> virtualenv-init.stderr
	if [ $? != 0 ]; then
		echo "failed! Cannot continue."
		exit -1
	else
		echo "done"
	fi
fi

source env/bin/activate

link_local_py_lib "lib/rpjios"

echo -n "* Installing modules from '${REQ_FILE}' (this may take awhile): "
pip install -r ${REQ_FILE} > pip-install.stdout 2> pip-install.stderr
echo "done"

if [ $? == 0 ]; then
	echo ""
	echo "*** Success! Run 'source env/bin/activate' to get started."
else
	echo "*** ERROR ***"
fi
