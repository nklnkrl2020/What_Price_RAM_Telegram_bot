package storage

import (
	"encoding/json"
	"os"
	"sync"
)

type Product struct {
	URL       string `json:"url"`
	LastPrice int    `json:"last_price"`
	MinPrice  int    `json:"min_price"`
	MaxPrice  int    `json:"max_price"`
}

type Data struct {
	Subscribers []int64   `json:"subscribers"`
	Products    []Product `json:"products"`
}

type Storage struct {
	file string
	mu   sync.Mutex
}

func NewStorage(file string) *Storage {
	return &Storage{file: file}
}

func (s *Storage) Load() (*Data, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	var data Data

	file, err := os.ReadFile(s.file)
	if err != nil {
		return &Data{}, nil
	}

	json.Unmarshal(file, &data)
	return &data, nil
}

func (s *Storage) Save(data *Data) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	bytes, _ := json.MarshalIndent(data, "", "  ")
	return os.WriteFile(s.file, bytes, 0644)
}
