async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width":1920,"height":1080})
        await page.wait_for_timeout(2500)
        print(f'URL: {page.url}')
        text = await page.locator('body').inner_text()
        print(f'BODY_START: {text[:700]}')
        if await page.locator('input').count() > 0 and ('sign' in text.lower() or 'welcome' in text.lower()):
            print('PASS: sign-in form controls rendered')
        else:
            print('FINDING: sign-in form controls did not render')
    except Exception as e:
        print(f'FINDING: sign-in route exception: {e}')
