FROM golang:1.21

WORKDIR /app

# Copy dependency files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN go build -o server .

# Expose the port
EXPOSE 8080

# Run the server
CMD ["./server"]
