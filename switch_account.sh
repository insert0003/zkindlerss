#!/bin/bash

mail=""
name=""

while [ $# -ge 2 ] ; do
        case "$1" in
                -m) mail=$2; shift 2;;
                -n) name=$2; shift 2;;
                *) echo "unknown parameter $1." ; 
                echo "usag: ./switch_account.sh -m mailAddr -n appName" ; exit 1 ; break;;
        esac
done

if [ "$mail" = "" ]; then
    echo "Please input your mail address."
    echo "usag: ./switch_account.sh -m mailAddr -n appName"
    exit 1
elif [ "$name" = "" ]; then
    echo "Please input your application name."
    echo "usag: ./switch_account.sh -m mailAddr -n appName"
    exit 1
fi

if ! [[ $mail =~ "@" ]]; then
    mail=$mail"@gmail.com"
fi

echo "MailAddress: ": $mail
echo "Application: ": $name

sed -i "s/application:/targetposition/g" app.yaml module-worker.yaml
sed -i "s/DOMAIN/targetposition/g" config.py
sed -i "/SRC_EMAIL/d" config.py

sed -i "/targetposition/iapplication:\ $name" app.yaml module-worker.yaml
sed -i "/targetposition/iSRC_EMAIL\ =\ \"$mail\"" config.py
sed -i "/targetposition/iDOMAIN\ =\ \"https:\/\/$name.appspot.com\"" config.py
sed -i "/targetposition/d" config.py app.yaml module-worker.yaml