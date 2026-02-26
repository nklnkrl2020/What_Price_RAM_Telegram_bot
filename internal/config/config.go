package config

import (
	"log"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	Token   string
	AdminID int64
}

func Load() *Config {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Ошибка загрузки .env")
	}

	adminID, err := strconv.ParseInt(os.Getenv("ADMIN_ID"), 10, 64)
	if err != nil {
		log.Fatal("ADMIN_ID неверный")
	}

	return &Config{
		Token:   os.Getenv("TOKEN"),
		AdminID: adminID,
	}
}
