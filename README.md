# AWSWAF - noisy neighbor

This function is used to process AWS WAF audio captcha "noisy neighbor" challenge.

# Dev

## Pre-requisites

> Assumed you have Python 3.10 installed already and have a virtual environment setup.

1. Install the requirements-dev.txt first
2. Install Azure functions core tools
3. Login `az login`

Run `func start`

# Deploy

`func azure functionapp publish awswafstt -b remote`
