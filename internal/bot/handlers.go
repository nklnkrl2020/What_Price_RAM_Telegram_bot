package bot

import (
	"fmt"
	"strconv"
	"strings"
	"sync"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"

	"price-bot/internal/parser"
	"price-bot/internal/storage"
)

type Handler struct {
	Bot     *tgbotapi.BotAPI
	Store   *storage.Storage
	AdminID int64

	waitingForURL map[int64]bool
	mu            sync.Mutex
}

func NewHandler(bot *tgbotapi.BotAPI, store *storage.Storage, adminID int64) *Handler {
	return &Handler{
		Bot:           bot,
		Store:         store,
		AdminID:       adminID,
		waitingForURL: make(map[int64]bool),
	}
}

func (h *Handler) Handle(update tgbotapi.Update) {

	if update.Message == nil {
		return
	}

	msg := update.Message
	userID := msg.From.ID
	text := msg.Text

	// =========================
	// Сначала команды
	// =========================
	if msg.IsCommand() {

		switch msg.Command() {

		case "start":
			h.subscribe(msg.Chat.ID, userID)

		case "products":
			h.listProducts(msg.Chat.ID)

		case "unsubscribe":
			h.unsubscribe(msg.Chat.ID, userID)

		case "add":
			if userID == h.AdminID {
				h.addProductFromCommand(msg.Chat.ID, text)
			} else {
				h.reply(msg.Chat.ID, "❌ Нет доступа")
			}

		case "remove":
			if userID == h.AdminID {
				h.removeProduct(msg.Chat.ID, text)
			} else {
				h.reply(msg.Chat.ID, "❌ Нет доступа")
			}

		default:
			h.reply(msg.Chat.ID, "Неизвестная команда")
		}

		return
	}

	// =========================
	// Если админ в режиме ожидания ссылки
	// =========================
	h.mu.Lock()
	waiting := h.waitingForURL[userID]
	h.mu.Unlock()

	if waiting {
		h.mu.Lock()
		h.waitingForURL[userID] = false
		h.mu.Unlock()

		h.addProductByURL(msg.Chat.ID, userID, text)
		return
	}

	// =========================
	// Кнопки
	// =========================
	switch text {

	case "📦 Товары":
		h.listProducts(msg.Chat.ID)

	case "❌ Отписаться":
		h.unsubscribe(msg.Chat.ID, userID)

	case "➕ Добавить":
		if userID != h.AdminID {
			h.reply(msg.Chat.ID, "❌ Нет доступа")
			return
		}

		h.mu.Lock()
		h.waitingForURL[userID] = true
		h.mu.Unlock()

		h.reply(msg.Chat.ID, "🔗 Отправь ссылку на товар")

	default:
		h.reply(msg.Chat.ID, "Не понимаю сообщение 🤔")
	}
}

func (h *Handler) reply(chatID int64, text string) {
	msg := tgbotapi.NewMessage(chatID, text)
	h.Bot.Send(msg)
}

func (h *Handler) subscribe(chatID int64, userID int64) {
	data, _ := h.Store.Load()

	for _, id := range data.Subscribers {
		if id == userID {
			msg := tgbotapi.NewMessage(chatID, "✅ Ты уже подписан!")
			msg.ReplyMarkup = MainKeyboard(userID == h.AdminID)
			h.Bot.Send(msg)
			return
		}
	}

	data.Subscribers = append(data.Subscribers, userID)
	h.Store.Save(data)

	msg := tgbotapi.NewMessage(chatID, "✅ Ты подписан на уведомления!")
	msg.ReplyMarkup = MainKeyboard(userID == h.AdminID)
	h.Bot.Send(msg)
}

func (h *Handler) unsubscribe(chatID int64, userID int64) {
	data, _ := h.Store.Load()

	newSubs := []int64{}
	found := false

	for _, id := range data.Subscribers {
		if id == userID {
			found = true
			continue
		}
		newSubs = append(newSubs, id)
	}

	if !found {
		h.reply(chatID, "Ты и так не подписан 🙂")
		return
	}

	data.Subscribers = newSubs
	h.Store.Save(data)

	h.reply(chatID, "❌ Ты отписался от уведомлений.")
}

// =========================
// Добавление через кнопку (ожидание ссылки)
// =========================
func (h *Handler) addProductByURL(chatID int64, userID int64, url string) {

	h.reply(chatID, "🔍 Проверяю цену...")

	price, err := parser.GetPrice(url)
	if err != nil {
		h.reply(chatID, "Ошибка получения цены")
		return
	}

	data, _ := h.Store.Load()

	for _, p := range data.Products {
		if p.URL == url {
			h.reply(chatID, "⚠ Этот товар уже отслеживается.")
			return
		}
	}

	data.Products = append(data.Products, storage.Product{
		URL:       url,
		LastPrice: price,
		MinPrice:  price,
		MaxPrice:  price,
	})

	h.Store.Save(data)

	h.reply(chatID, fmt.Sprintf("✅ Товар добавлен\nЦена: %d ₽", price))
}

// =========================
// Добавление через команду /add
// =========================
func (h *Handler) addProductFromCommand(chatID int64, text string) {
	parts := strings.Split(text, " ")
	if len(parts) < 2 {
		h.reply(chatID, "Использование: /add ссылка")
		return
	}
	h.addProductByURL(chatID, h.AdminID, parts[1])
}

func (h *Handler) listProducts(chatID int64) {
	data, _ := h.Store.Load()

	if len(data.Products) == 0 {
		h.reply(chatID, "Нет добавленных товаров")
		return
	}

	var builder strings.Builder
	builder.WriteString("📦 Отслеживаемые товары:\n\n")

	for i, p := range data.Products {
		builder.WriteString(fmt.Sprintf(
			"%d. %s\n   Текущая: %d ₽\n   Мин: %d ₽ | Макс: %d ₽\n\n",
			i+1,
			p.URL,
			p.LastPrice,
			p.MinPrice,
			p.MaxPrice,
		))
	}

	h.reply(chatID, builder.String())
}

func (h *Handler) removeProduct(chatID int64, text string) {
	parts := strings.Split(text, " ")
	if len(parts) < 2 {
		h.reply(chatID, "Использование: /remove номер")
		return
	}

	index, err := strconv.Atoi(parts[1])
	if err != nil {
		h.reply(chatID, "Нужно указать число")
		return
	}

	data, _ := h.Store.Load()

	if index < 1 || index > len(data.Products) {
		h.reply(chatID, "Товара с таким номером нет")
		return
	}

	removed := data.Products[index-1]
	data.Products = append(data.Products[:index-1], data.Products[index:]...)
	h.Store.Save(data)

	h.reply(chatID, fmt.Sprintf("❌ Удалён:\n%s", removed.URL))
}