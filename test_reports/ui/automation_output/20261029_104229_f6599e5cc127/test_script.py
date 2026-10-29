async def run_test(page, output_dir, page_url):
    import re
    try:
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.wait_for_selector('[data-testid="hero-shop-button"]', timeout=10000)
        print('PASS: storefront loaded with hero CTA')
        await page.wait_for_selector('[data-testid^="product-card-"]', timeout=10000)
        cards = await page.locator('[data-testid^="product-card-"]').count()
        print(f'PASS: product cards rendered ({cards})')
        await page.locator('[data-testid="product-search-input"]').fill('Quiet')
        await page.wait_for_timeout(300)
        visible_cards = await page.locator('[data-testid^="product-card-"]:visible').count()
        if visible_cards == 1:
            print('PASS: product search filters results')
        else:
            print(f'FINDING: product search expected one visible result, found {visible_cards}')
        await page.locator('[data-testid="product-search-input"]').fill('')
        await page.locator('[data-testid="category-workbooks"]').click()
        await page.wait_for_timeout(300)
        visible_cards = await page.locator('[data-testid^="product-card-"]:visible').count()
        if visible_cards == 1:
            print('PASS: category filtering works')
        else:
            print(f'FINDING: category filter expected one visible result, found {visible_cards}')
        await page.locator('[data-testid="product-card-weekly-reset"] .product-image').click()
        await page.wait_for_timeout(700)
        if '/product/weekly-reset' in page.url:
            print('PASS: product card navigated to detail route')
        else:
            print(f'FINDING: product card navigation landed at {page.url}')
        detail_error = await page.locator('body').inner_text()
        if 'Product not found' in detail_error or 'Loading the good stuff' in detail_error:
            print('FINDING: product detail did not render product content')
        else:
            print('PASS: product detail content rendered')
        await page.goto('https://dream-income-2--02t0oetm.preview.emergentagent.com/')
        await page.wait_for_selector('[data-testid="product-card-weekly-reset"]', timeout=10000)
        await page.locator('[data-testid="product-card-weekly-reset"] .product-image').click()
        await page.wait_for_timeout(500)
        buy = page.locator('[data-testid="buy-product-button"]')
        if await buy.count():
            await buy.click()
            await page.wait_for_timeout(500)
            email = page.locator('[data-testid="checkout-email-input"]')
            if await email.count():
                await email.fill('test-ui@example.com')
                await page.locator('[data-testid="checkout-submit-button"]').click()
                await page.wait_for_timeout(900)
                if '/payment/success?session_id=' in page.url and await page.locator('[data-testid="download-product-button"]').count():
                    print('PASS: demo checkout and success download link work')
                else:
                    print(f'FINDING: checkout success flow failed at {page.url}')
            else:
                print('FINDING: checkout email input missing')
        else:
            print('FINDING: buy button missing because detail page failed')
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.goto('https://dream-income-2--02t0oetm.preview.emergentagent.com/')
        await page.wait_for_selector('[data-testid="hero-shop-button"]', timeout=10000)
        overflow = await page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        if overflow:
            print('FINDING: mobile layout has horizontal overflow')
        else:
            print('PASS: mobile layout has no horizontal overflow')
        error_text = await page.evaluate("""() => { const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]')); return errorElements.map(el => el.textContent).join(', '); }""")
        if error_text:
            print(f'Found error message: {error_text}')
        else:
            print('No error messages found on the page')
    except Exception as e:
        print(f'FINDING: UI test exception: {e}')
