package bot

import tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"

const (
	SUBSCRIBE = 	"✅ Подписаться"
	RUN = 			"🚀 Запуск"
	ADD = 			"➕ Добавить"
	PRODUCTS = 		"📦 Товары"
	DELETE = 		"❌ Удалить"
	UNSUBSCRIBE = 	"❌ Отписаться"
)

func MainKeyboard(isAdmin bool) tgbotapi.ReplyKeyboardMarkup {

	var rows [][]tgbotapi.KeyboardButton

	if isAdmin {
		rows = [][]tgbotapi.KeyboardButton{
			{
				tgbotapi.NewKeyboardButton(SUBSCRIBE),
			},
			{
				tgbotapi.NewKeyboardButton(RUN),
			},
			{
				tgbotapi.NewKeyboardButton(ADD),
			},
			{
				tgbotapi.NewKeyboardButton(PRODUCTS),
			},
			{
				tgbotapi.NewKeyboardButton(DELETE),
			},
			{
				tgbotapi.NewKeyboardButton(UNSUBSCRIBE),
			},
		}
	} else {
		rows = [][]tgbotapi.KeyboardButton{
			{
				tgbotapi.NewKeyboardButton(SUBSCRIBE),
			},
			{
				tgbotapi.NewKeyboardButton(PRODUCTS),
			},
			{
				tgbotapi.NewKeyboardButton(UNSUBSCRIBE),
			},
		}
	}

	return tgbotapi.ReplyKeyboardMarkup{
		Keyboard:       rows,
		ResizeKeyboard: true,
	}
}
