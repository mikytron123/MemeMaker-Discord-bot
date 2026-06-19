lint:
    isort --profile black .
    find . -name '*.py' -exec pyupgrade {} +
    autoflake -i --remove-all-unused-imports --ignore-init-module-imports --remove-duplicate-keys --remove-unused-variables -r .
    flake8 --extend-ignore=E501,B008,SIM113

format:
    black .