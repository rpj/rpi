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
		echo "* Trying to install '${_N}..."
		sudo apt -y install ${_N}
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
	echo -n "* Building embedded-sps submodule: "
	git submodule init
	git submodule update --recursive
	pushd embedded-sps > /dev/null
	pushd embedded-common > /dev/null
	git submodule init
	git submodule update --recursive
	popd > /dev/null
	make release > make.release.stdout 2> make.release.stderr
	pushd release/sps30-i2c > /dev/null
	pushd hw_i2c > /dev/null
	mv sensirion_hw_i2c_implementation.c sensirion_hw_i2c_implementation.c.orig
	ln -s sample-implementations/linux_user_space/sensirion_hw_i2c_implementation.c
	popd > /dev/null
	make > make.stdout 2> make.stderr
	popd > /dev/null
	popd > /dev/null
	echo "done"
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
check_and_install "which" "redis-server" "redis"
check_and_install "apt" "python-dev"

if [ ${IS_RPI} == 1 ]; then
	check_and_install "apt" "python-smbus"
	build_embedded_sps
fi

if [ ! -d "./env" ]; then
	echo "* Initializing virtualenv:"
	virtualenv --system-site-packages --prompt="(rpjios virtualenv) " ./env
fi

source env/bin/activate

link_local_py_lib "lib/rpjios"

echo -n "* Installing required python modules from '${REQ_FILE}': "
pip install -r ${REQ_FILE} > pip-install.stdout 2> pip-install.stderr
echo "done"

if [ $? == 0 ]; then
	echo ""
	echo "*** Success! Run 'source env/bin/activate' to get started."
else
	echo "*** ERROR ***"
fi
