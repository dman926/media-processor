BINARY_NAME=media-processor

all: build test

build:
	go build -ldflags '-w -s' -o ${BINARY_NAME} main.go

test:
  go test -v main.go

run: build
  ./${BINARY_NAME}

clean:
  go clean
  rm ${BINARY_NAME}