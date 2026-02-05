package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
)

type HealthResponse struct {
	Status    string    `json:"status"`
	Timestamp time.Time `json:"timestamp"`
}

type InfoResponse struct {
	Service string `json:"service"`
	Version string `json:"version"`
	Go      string `json:"go_version"`
}

type EchoRequest struct {
	Message string `json:"message"`
}

type EchoResponse struct {
	Original  string    `json:"original"`
	Echo      string    `json:"echo"`
	Timestamp time.Time `json:"timestamp"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	response := HealthResponse{
		Status:    "healthy",
		Timestamp: time.Now(),
	}
	
	json.NewEncoder(w).Encode(response)
}

func infoHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	response := InfoResponse{
		Service: "go-api",
		Version: "1.0.0",
		Go:      "1.21",
	}
	
	json.NewEncoder(w).Encode(response)
}

func echoHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	
	var req EchoRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}
	
	response := EchoResponse{
		Original:  req.Message,
		Echo:      fmt.Sprintf("Echo: %s", req.Message),
		Timestamp: time.Now(),
	}
	
	json.NewEncoder(w).Encode(response)
}

func main() {
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/info", infoHandler)
	http.HandleFunc("/echo", echoHandler)
	
	port := ":8080"
	log.Printf("Server starting on port %s", port)
	log.Printf("Health check: http://localhost%s/health", port)
	log.Printf("Info: http://localhost%s/info", port)
	log.Printf("Echo: POST to http://localhost%s/echo", port)
	
	if err := http.ListenAndServe(port, nil); err != nil {
		log.Fatal(err)
	}
}
