package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/ssm"
	"github.com/aws/aws-sdk-go-v2/service/ssm/types"
	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"
	"google.golang.org/api/calendar/v3"
	"google.golang.org/api/option"
)

type CalendarEvent struct {
	DateTime string `json:"dateTime"`
	Summary  string `json:"summary"`
}

type Config struct {
	GoogleAPIOAuthToken  string
	GoogleAPICredentials string
}

var ssmClient *ssm.Client
var googleAPICreds Config
var numEvents int64

// Gets a value from SSM Parameter Store.
func getValueFromSSM(ssmParamName string) (string, error) {
	input := &ssm.GetParameterInput{
		Name:           aws.String(ssmParamName),
		WithDecryption: aws.Bool(true),
	}
	result, err := ssmClient.GetParameter(context.TODO(), input)
	if err != nil {
		return "", err
	}
	return *result.Parameter.Value, err
}

// Saves a value to SSM Parameter Store.
func saveValueToSSM(ssmParamName string, value string) error {
	input := &ssm.PutParameterInput{
		Name:      aws.String(ssmParamName),
		Type:      types.ParameterTypeSecureString,
		Value:     aws.String(value),
		Overwrite: aws.Bool(true),
	}
	_, err := ssmClient.PutParameter(context.TODO(), input)
	if err != nil {
		return err
	}
	return nil
}

// Retrieves an OAuth Google API token, refreshes it, saves the refreshed token, and returns the generated client.
func getClient(config *oauth2.Config) (*http.Client, error) {
	ssmParamName := googleAPICreds.GoogleAPIOAuthToken
	rawJSON, err := getValueFromSSM(ssmParamName)
	if err != nil {
		return nil, fmt.Errorf("failed to get %s, %w", ssmParamName, err)
	}
	tok := &oauth2.Token{}
	err = json.Unmarshal([]byte(rawJSON), tok)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal the token from JSON: %w", err)
	}
	// Create a new TokenSource that automatically refreshes the token as necessary.
	tokenSource := config.TokenSource(context.Background(), tok)

	// Get the refreshed token.
	tok, err = tokenSource.Token()
	if err != nil {
		return nil, fmt.Errorf("failed to refresh token: %w", err)
	}

	tokenJson, err := json.Marshal(tok)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal the token to JSON: %v", err)
	}
	// Save the token back to SSM, regardless of whether it has been refreshed or not.
	err = saveValueToSSM(ssmParamName, string(tokenJson))
	if err != nil {
		return nil, fmt.Errorf("failed to save token to %s parameter: %w", ssmParamName, err)
	}

	// Create a new HTTP client with the TokenSource.
	client := oauth2.NewClient(context.Background(), tokenSource)

	return client, nil
}

// Retrieves the calendar ID for a given calendar name from the Google Calendar service.
func getCalendarID(calendarService *calendar.Service, calendarName string) (string, error) {
	pageToken := ""
	for {
		calendarList, err := calendarService.CalendarList.List().PageToken(pageToken).Do()
		if err != nil {
			return "", err
		}
		for _, item := range calendarList.Items {
			if item.Summary == calendarName {
				return item.Id, nil
			}
		}
		pageToken = calendarList.NextPageToken
		if pageToken == "" {
			break
		}
	}
	return "", fmt.Errorf("failed to find the calendarID by name: %v", calendarName)
}

func HandleRequest(ctx context.Context, request events.APIGatewayV2HTTPRequest) (events.APIGatewayProxyResponse, error) {
	calendarName := request.PathParameters["calendar-name"]
	if calendarName == "" {
		return events.APIGatewayProxyResponse{
				StatusCode: http.StatusBadRequest,
			},
			fmt.Errorf("calendar name is empty or not provided")
	}

	if request.QueryStringParameters["num-events"] != "" {
		parsedInt, err := strconv.ParseInt(request.QueryStringParameters["num-events"], 10, 64)
		if err != nil {
			return events.APIGatewayProxyResponse{
					StatusCode: http.StatusBadRequest,
				},
				fmt.Errorf("failed to parse number of calendar events: %w", err)
		}
		numEvents = parsedInt
	}

	secretName := googleAPICreds.GoogleAPICredentials
	googleApiCredentials, err := getValueFromSSM(secretName)
	if err != nil {
		return events.APIGatewayProxyResponse{
				StatusCode: http.StatusInternalServerError,
			},
			fmt.Errorf("failed to read secret %v from AWS SSM Parameter Store: %w", secretName, err)
	}
	googleAPIConfig, err := google.ConfigFromJSON([]byte(googleApiCredentials), calendar.CalendarReadonlyScope)
	if err != nil {
		return events.APIGatewayProxyResponse{
				StatusCode: http.StatusInternalServerError,
			},
			fmt.Errorf("failed to parse client secret file to googleAPIConfig: %w", err)
	}

	client, err := getClient(googleAPIConfig)
	if err != nil {
		return events.APIGatewayProxyResponse{
				StatusCode: http.StatusInternalServerError,
			},
			fmt.Errorf("failed to get client: %w", err)
	}

	calendarService, err := calendar.NewService(ctx, option.WithHTTPClient(client))
	if err != nil {
		return events.APIGatewayProxyResponse{
			StatusCode: http.StatusInternalServerError,
		}, fmt.Errorf("failed to retrieve Calendar client: %w", err)
	}

	calendarID, err := getCalendarID(calendarService, string(calendarName))
	if err != nil {
		return events.APIGatewayProxyResponse{
			StatusCode: http.StatusInternalServerError,
		}, fmt.Errorf("failed to get calendar ID: %w", err)
	}

	calendarEvents, err := calendarService.Events.List(calendarID).
		ShowDeleted(false).
		SingleEvents(true).
		TimeMin(time.Now().Format(time.RFC3339)).
		MaxResults(numEvents).
		OrderBy("startTime").Do()
	if err != nil {
		return events.APIGatewayProxyResponse{
			StatusCode: http.StatusInternalServerError,
		}, fmt.Errorf("failed to retrieve events from the calendar %v: %w", calendarID, err)
	}

	var eventsList []CalendarEvent
	for _, item := range calendarEvents.Items {
		var formattedDate string
		if item.Start.DateTime != "" {
			parsedDate, err := time.Parse(time.RFC3339, item.Start.DateTime)
			if err != nil {
				return events.APIGatewayProxyResponse{
					StatusCode: http.StatusInternalServerError,
				}, fmt.Errorf("failed to parse date: %w", err)
			}
			formattedDate = parsedDate.Format("02.Jan.15:04")
		} else {
			parsedDate, err := time.Parse("2006-01-02", item.Start.Date)
			if err != nil {
				return events.APIGatewayProxyResponse{
					StatusCode: http.StatusInternalServerError,
				}, fmt.Errorf("failed to parse date: %w", err)
			}
			formattedDate = parsedDate.Format("02.Jan")
		}

		eventsList = append(eventsList, CalendarEvent{
			DateTime: formattedDate,
			Summary:  item.Summary,
		})
	}

	jsonEvents, err := json.Marshal(eventsList)
	if err != nil {
		return events.APIGatewayProxyResponse{
			StatusCode: http.StatusInternalServerError,
		}, fmt.Errorf("failed to marshal events to JSON: %w", err)
	}

	return events.APIGatewayProxyResponse{
			StatusCode: http.StatusOK,
			Body:       string(jsonEvents),
			Headers:    map[string]string{"Content-Type": "application/json"},
		},
		nil
}

// init initializes the application by setting up the Google API credentials and loading the AWS SDK config.
func init() {
	// Set up Google API credentials
	googleAPICreds = Config{
		GoogleAPIOAuthToken:  os.Getenv("GOOGLE_API_OAUTH_TOKEN"),
		GoogleAPICredentials: os.Getenv("GOOGLE_API_CREDENTIALS"),
	}

	// Set up the default number of events to be returned
	numEvents = 5

	// Load AWS SDK config
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("failed to load the AWS SDK config: %v", err)
	}
	ssmClient = ssm.NewFromConfig(cfg)
}

func main() {
	lambda.Start(HandleRequest)
}
