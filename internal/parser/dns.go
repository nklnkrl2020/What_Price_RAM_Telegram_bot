// package parser

// import (
// 	"net/http"
// 	"strconv"
// 	"strings"

// 	"github.com/PuerkitoBio/goquery"
// )

// func GetPrice(url string) (int, error) {
// 	resp, err := http.Get(url)
// 	if err != nil {
// 		return 0, err
// 	}
// 	defer resp.Body.Close()

// 	doc, err := goquery.NewDocumentFromReader(resp.Body)
// 	if err != nil {
// 		return 0, err
// 	}

// 	priceText := doc.Find(".product-buy__price").First().Text()

// 	clean := strings.ReplaceAll(priceText, "₽", "")
// 	clean = strings.ReplaceAll(clean, " ", "")

// 	price, err := strconv.Atoi(clean)
// 	if err != nil {
// 		return 0, err
// 	}

// 	return price, nil
// }

package parser

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/chromedp/chromedp"
)

func GetPrice(url string) (int, error) {

	// Создаём контекст Chrome
	ctx, cancel := chromedp.NewExecAllocator(context.Background(),
		//chromedp.Headless,
		chromedp.DisableGPU,
		chromedp.NoSandbox,
		chromedp.Flag("disable-dev-shm-usage", true),
		chromedp.Flag("disable-blink-features", "AutomationControlled"),
	)
	defer cancel()

	ctx, cancel = chromedp.NewContext(ctx)
	defer cancel()

	// Таймаут 30 секунд
	ctx, cancel = context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	var priceText string

	err := chromedp.Run(ctx,
		// Открываем главную страницу (как в Python)
		chromedp.Navigate("https://www.dns-shop.ru/"),
		chromedp.Sleep(4*time.Second),

		// Переходим на страницу товара
		chromedp.Navigate(url),
		chromedp.Sleep(6*time.Second),

		// Скролл
		chromedp.Evaluate(`window.scrollTo(0, document.body.scrollHeight/2);`, nil),
		chromedp.Sleep(3*time.Second),

		// Ждём появления цены
		chromedp.WaitVisible(".product-buy__price"),

		// Забираем текст
		chromedp.Text(".product-buy__price", &priceText),
	)

	if err != nil {
		return 0, fmt.Errorf("ошибка получения цены: %w", err)
	}

	// Чистим строку
	clean := strings.ReplaceAll(priceText, "₽", "")
	clean = strings.ReplaceAll(clean, " ", "")
	clean = strings.TrimSpace(clean)

	price, err := strconv.Atoi(clean)
	if err != nil {
		return 0, fmt.Errorf("ошибка конвертации цены: %w", err)
	}

	return price, nil
}