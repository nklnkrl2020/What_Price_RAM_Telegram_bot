package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"

	"price-bot/internal/config"
	"price-bot/internal/storage"
	botpkg "price-bot/internal/bot"
)

func main() {

	// =========================
	// Загрузка конфигурации
	// =========================
	cfg := config.Load()

	// =========================
	// Инициализация storage
	// =========================
	store := storage.NewStorage("data/products.json")

	// =========================
	// Создание Telegram бота
	// =========================
	tgbot, err := tgbotapi.NewBotAPI(cfg.Token)
	if err != nil {
		log.Fatal("Ошибка создания бота:", err)
	}

	tgbot.Debug = false
	log.Printf("Бот запущен: @%s\n", tgbot.Self.UserName)

	// =========================
	// УСТАНОВКА НОВОГО МЕНЮ (квадратики справа)
	// =========================
	// commands := []tgbotapi.BotCommand{
	// 	{Command: "start", Description: "Запуск бота"},
	// 	{Command: "products", Description: "Список товаров"},
	// 	{Command: "add", Description: "Добавить товар (админ)"},
	// 	{Command: "remove", Description: "Удалить товар (админ)"},
	// 	{Command: "unsubscribe", Description: "Отписаться"},
	// }

	// cfgCmd := tgbotapi.NewSetMyCommands(commands...)
	// _, err = tgbot.Request(cfgCmd)
	// if err != nil {
	// 	log.Fatal("Ошибка установки меню:", err)
	// }

	// =========================
	// Создание handler
	// =========================
	handler := botpkg.NewHandler(tgbot, store, cfg.AdminID)

	// =========================
	// Контекст для graceful shutdown
	// =========================
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// =========================
	// Запуск планировщика цен
	// =========================
	go startScheduler(ctx, tgbot, store)

	// =========================
	// Настройка polling
	// =========================
	updateConfig := tgbotapi.NewUpdate(0)
	updateConfig.Timeout = 60

	updates := tgbot.GetUpdatesChan(updateConfig)

	// =========================
	// Обработка сигналов завершения
	// =========================
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-stop
		log.Println("Остановка бота...")
		cancel()
		tgbot.StopReceivingUpdates()
	}()

	// =========================
	// Основной цикл обработки сообщений
	// =========================
	for update := range updates {
		if update.Message == nil {
			continue
		}

		go handler.Handle(update)
	}

	log.Println("Бот остановлен")
}

// =========================
// Планировщик проверки цен
// =========================
func startScheduler(ctx context.Context, bot *tgbotapi.BotAPI, store *storage.Storage) {

	ticker := time.NewTicker(24 * time.Hour)
	defer ticker.Stop()

	time.Sleep(10 * time.Second)

	for {
		select {
		case <-ctx.Done():
			log.Println("Scheduler остановлен")
			return

		case <-ticker.C:
			log.Println("Запуск проверки цен...")
			botpkg.CheckPrices(bot, store)
		}
	}
}