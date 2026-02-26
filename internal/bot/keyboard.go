package bot

import tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"

func MainKeyboard(isAdmin bool) tgbotapi.ReplyKeyboardMarkup {

	var rows [][]tgbotapi.KeyboardButton

	if isAdmin {
		rows = [][]tgbotapi.KeyboardButton{
			{
				tgbotapi.NewKeyboardButton("➕ Добавить"),
			},
			{
				tgbotapi.NewKeyboardButton("📦 Товары"),
			},
			{
				tgbotapi.NewKeyboardButton("❌ Удалить"),
			},
			{
				tgbotapi.NewKeyboardButton("❌ Отписаться"),
			},
		}
	} else {
		rows = [][]tgbotapi.KeyboardButton{
			{
				tgbotapi.NewKeyboardButton("📦 Товары"),
			},
			{
				tgbotapi.NewKeyboardButton("❌ Отписаться"),
			},
		}
	}

	return tgbotapi.ReplyKeyboardMarkup{
		Keyboard:       rows,
		ResizeKeyboard: true,
	}
}
