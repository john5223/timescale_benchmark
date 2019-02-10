FROM golang:1.8.3-alpine

RUN apk add --no-cache git
RUN go get -v github.com/gocelery/gocelery
RUN apk del git

COPY worker.go/ .

ENV PORT=3001
CMD ["go", "run", "main.go"]

#RUN apk -Uuv add openssl
#RUN sh "$(pwd)/ssl/install.sh"
#RUN go build .
#EXPOSE 80 443