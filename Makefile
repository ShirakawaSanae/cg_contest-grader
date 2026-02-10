VERSION = `python -m pygrading version`
PACKAGE_PATH = package/${VERSION}
DEV_PATH = temp

setup:
	###########################################
	##         Setup PyGrading Wheel         ##
	###########################################
	python setup.py sdist bdist_wheel

	rm -rf build
	rm -rf pygrading.egg-info

	mkdir -p package
	rm -rf ${PACKAGE_PATH}
	mv dist ${PACKAGE_PATH}


dev: setup
	###########################################
	##         Init development env          ##
	###########################################
	pip uninstall -y pygrading
	pip install ${PACKAGE_PATH}/*.whl

	rm -rf cg_kernel
	python -m pygrading init
	

upload: setup

	###########################################
	##         Upload PyGrading Wheel        ##
	###########################################
	python -m twine upload ${PACKAGE_PATH}/*
