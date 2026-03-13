package bot

import (
	"fmt"
	"log"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"

	"price-bot/internal/parser"
	"price-bot/internal/storage"
)

func CheckPrices(bot *tgbotapi.BotAPI, store *storage.Storage) {
	data, err := store.Load()
	if err != nil {
		log.Println("Ошибка загрузки данных:", err)
		return
	}

	if len(data.Products) == 0 {
		log.Println("Нет товаров для проверки")
		return
	}

	ctx,cancelctx := parser.NewBrowser()
	defer cancelctx()

	for i, product := range data.Products {

		log.Println("Проверяем:", product.URL)

		newPrice, err := parser.GetPrice(ctx,product.URL)
		if err != nil {
			log.Println("Ошибка получения цены:", err)
			continue
		}

		oldPrice := product.LastPrice
		diff := newPrice - oldPrice

		// Обновляем статистику
		if newPrice < product.MinPrice {
			product.MinPrice = newPrice
		}
		if newPrice > product.MaxPrice {
			product.MaxPrice = newPrice
		}

		product.LastPrice = newPrice
		data.Products[i] = product

		// Формируем сообщение
		var message string

		if diff == 0 {
			message = fmt.Sprintf(
				"📦 Цена не изменилась\n\n%s\n\nТекущая: %d ₽",
				product.URL,
				newPrice,
			)
		} else if diff > 0 {
			message = fmt.Sprintf(
				"📈 Цена выросла на %d ₽\n\n%s\n\nСейчас: %d ₽",
				diff,
				product.URL,
				newPrice,
			)
		} else {
			message = fmt.Sprintf(
				"📉 Цена снизилась на %d ₽\n\n%s\n\nСейчас: %d ₽",
				-diff,
				product.URL,
				newPrice,
			)
		}

		message += fmt.Sprintf(
			"\n\nМинимальная: %d ₽\nМаксимальная: %d ₽",
			product.MinPrice,
			product.MaxPrice,
		)

		// Рассылка подписчикам
		for _, subscriber := range data.Subscribers {
			msg := tgbotapi.NewMessage(subscriber, message)
			_, err := bot.Send(msg)
			if err != nil {
				log.Println("Ошибка отправки:", err)
			}
		}
	}

	// Сохраняем обновлённые цены
	err = store.Save(data)
	if err != nil {
		log.Println("Ошибка сохранения:", err)
	}

	log.Println("Проверка цен завершена")
}
