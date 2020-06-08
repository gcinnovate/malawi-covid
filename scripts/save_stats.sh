#!/usr/bin/env bash

# This is run as a cron job every 30 minutes
# */30 * * * *  /root/refresh_piecharts.sh

cd /var/www/malawi-covid
source /var/www/envs/malawi-covid/bin/activate
source .env
flask save-statistics
