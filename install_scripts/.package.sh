#!/bin/bash

if_not_dir_create () {
  if [ ! -d "$1" ]; then
  mkdir -p "$1"
  fi
}

declare -a outputs=("deb" "rpm" "sh")
declare -a pypacks=("astral" "requests" "tz" "tzlocal" "schedule")
declare -a otherdeps=("python3-pip")
declare -a python_versions=("3.5" "3.6" "3.7")

declare -a original_files=(*)

deps=""
for p in "${pypacks[@]}"
do
	deps="$deps-d python3-$p "
done

for d in "${otherdeps[@]}"
do
	deps="$deps-d $d "
done

for pyth_v in "${python_versions[@]}"; do
	# NO_DEPS PACKAGING
	for out in "${outputs[@]}"
	do
		fpm -s python -t "${out}" -f -n 'automathemely' --python-bin python${pyth_v} --python-pip pip3 \
		--python-package-name-prefix python3 --no-python-dependencies --after-install postinst.sh \
		--before-remove preremove.sh ../setup.py
	done

	for file in *; do
		if [[ ! " ${original_files[@]} " =~ " ${file} " ]]; then
			mv "$file" "no_deps-${file}"
		fi
	done

	# DEPS PACKAGING
	for out in "${outputs[@]}"
	do
		fpm -s python -t "${out}" -f -n 'automathemely' --python-bin python${pyth_v} --python-pip pip3 \
		--python-package-name-prefix python3 --no-python-dependencies ${deps}--after-install postinst.sh \
		--before-remove preremove.sh ../setup.py
	done

	for file in *; do
		if [[ ! " ${original_files[@]} " =~ " ${file} " ]]; then
			mv "$file" "python${pyth_v}-${file}"
		fi
	done

	version="$(echo python${pyth_v}-automathemely*.deb | grep -o -P '(?<=_).*(?=_)')"

	if [ "$version" != "" ]
	then
		if_not_dir_create "../releases/python${pyth_v}/v$version"
		mv *automathemely* "../releases/python${pyth_v}/v$version"
	fi
done
