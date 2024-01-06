#!/bin/zsh

rm -rf deployment.zip bootstrap
GOOS=linux GOARCH=arm64 go build -tags lambda.norpc -o bootstrap main.go
zip deployment.zip bootstrap