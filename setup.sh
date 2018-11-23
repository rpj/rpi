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
		ln -s "../../../../${LIBDIR}"
		popd > /dev/null
	fi
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
	echo "* Looks like you're installing on a non-RPi platform; omitting unneeded modules."
	IS_RPI=0
	REQ_FILE=requirements-nonRPi.txt
fi

check_and_install "which" "virtualenv"
check_and_install "which" "redis-server" "redis"
check_and_install "apt" "python-dev"

if [ ${IS_RPI} == 1 ]; then
	check_and_install "apt" "python-smbus"
fi

if [ ! -d "./env" ]; then
	echo "* Initializing virtualenv:"
	virtualenv --system-site-packages --prompt="(rpjios virtualenv) " ./env
fi

source env/bin/activate

link_local_py_lib "lib/rpjios"

echo -n "* Installing required python modules from '${REQ_FILE}': "
pip install -r ${REQ_FILE}

if [ $? == 0 ]; then
	echo ""
	echo "*** Done! Run 'source env/bin/activate' to get started."
else
	echo "*** ERROR ***"
fi
