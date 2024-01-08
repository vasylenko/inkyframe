FROM golang:1.21.5 AS builder
WORKDIR /build
COPY go.mod go.sum main.go ./
RUN go build -tags lambda.norpc -o apigw-authorizer main.go

FROM public.ecr.aws/lambda/provided:al2023-arm64
COPY --from=builder /build/apigw-authorizer /apigw-authorizer
ENTRYPOINT ["/apigw-authorizer"]
