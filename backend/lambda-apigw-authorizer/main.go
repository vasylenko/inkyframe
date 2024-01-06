package main

import (
	"context"
	"log"
	"os"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/ssm"
)

var ssmClient *ssm.Client

func getSSMParameter(ctx context.Context, parameterName string) (string, error) {
	input := &ssm.GetParameterInput{
		Name:           &parameterName,
		WithDecryption: aws.Bool(true),
	}

	param, err := ssmClient.GetParameter(ctx, input)
	if err != nil {
		return "", err
	}

	return *param.Parameter.Value, nil
}

func handler(ctx context.Context, request events.APIGatewayV2CustomAuthorizerV2Request) (events.APIGatewayV2CustomAuthorizerSimpleResponse, error) {
	response := events.APIGatewayV2CustomAuthorizerSimpleResponse{IsAuthorized: false}

	authorizationValue, err := getSSMParameter(ctx, os.Getenv("AUTHORIZATION_TOKEN"))
	if err != nil {
		log.Printf("failed to get the SSM parameter: %v", err)
		return response, err
	}

	sourceIP := request.Headers["x-forwarded-for"]

	if request.Headers["authorization"] == authorizationValue {
		log.Printf("handler - successfull authorization for %s", sourceIP)
		response.IsAuthorized = true
		return response, nil
	}

	log.Printf("handler - authorization failed for %s", sourceIP)
	return response, nil
}

func init() {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("failed to load the config: %v", err)
	}

	ssmClient = ssm.NewFromConfig(cfg)

	if os.Getenv("AUTHORIZATION_TOKEN") == "" {
		log.Fatalf("environment variable AUTHORIZATION_TOKEN is not set")
	}
}

func main() {
	lambda.Start(handler)
}
