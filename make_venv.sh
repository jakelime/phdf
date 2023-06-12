#!/usr/local/bin/bash
PYTHON_VERSION='3.10'
NEW_ENV_NAME='autoScriptTemp'
PYTHON_VENV_NAME='venv'

create_conda_environment() {
    echo $(conda --version)
    conda create -n $NEW_ENV_NAME python=$PYTHON_VERSION <<EOF
y
EOF
    eval "$(conda shell.bash hook)"
    conda activate "$NEW_ENV_NAME"
    echo "conda env created: $(python3 --version)"
}

remove_conda_environment() {
    conda deactivate
    conda remove -n "$NEW_ENV_NAME" --all <<EOF
y
EOF

}

create_python_environment() {

    create_conda_environment

    if [[ -d "venv" ]]; then
        echo "removing existing $PYTHON_VENV_NAME..."
        rm -rf "$PYTHON_VENV_NAME"
    fi
    echo "using python here: $(which python3); $(python --version)"
    python3 -m venv "$PYTHON_VENV_NAME" --copies

    remove_conda_environment
}

install_python_libraries_minimum() {
    # Installs the minimum libraries required to run, with pyinstaller to package
    source "$PYTHON_VENV_NAME/bin/activate"
    echo "using python here: $(which python3); $(python --version)"
    pip install --upgrade pip
    # Bare minimum installation
    pip install tables
    pip install pandas
    pip install pyinstaller
    deactivate
}

install_python_libraries_full() {
    # Installs the minimum libraries required to run, with pyinstaller to package
    source "$PYTHON_VENV_NAME/bin/activate"
    echo "using python here: $(which python3); $(python --version)"
    pip install --upgrade pip
    # Bare minimum installation
    pip install tables
    pip install pandas
    # To run automated tests, automated distribute using SSH
    pip install pytest
    pip install python-dotenv
    pip install paramiko
    pip install pyinstaller
    deactivate
}

main() {
    local installMode="$(tr [A-Z] [a-z] <<< "$1")" # converts to lowercase

    create_python_environment

    if [[ "$installMode" == "full" ]]; then
        echo "installMode is $installMode"
        install_python_libraries_full
    else
        echo "installMode is $installMode"
        install_python_libraries_minimum
    fi

}

main $1
