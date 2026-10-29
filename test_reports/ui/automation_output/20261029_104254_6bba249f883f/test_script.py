async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.wait_for_selector('[data-testid="admin-sign-in-button"]', timeout=10000)
        print('PASS: signed-out owner route renders protection wall')
        await page.goto('https://dream-income-2--02t0oetm.preview.emergentagent.com/sign-in')
        await page.wait_for_timeout(1500)
        body = await page.locator('body').inner_text()
        if 'Sign in' in body or 'Welcome' in body:
            print('PASS: Clerk sign-in route rendered')
        else:
            print('FINDING: Clerk sign-in route has no sign-in UI')
        await page.goto('https://dream-income-2--02t0oetm.preview.emergentagent.com/sign-up')
        await page.wait_for_timeout(1500)
        body = await page.locator('body').inner_text()
        if 'Sign up' in body or 'Create' in body:
            print('PASS: Clerk sign-up route rendered')
        else:
            print('FINDING: Clerk sign-up route has no sign-up UI')
        error_text = await page.evaluate("""() => { const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]')); return errorElements.map(el => el.textContent).join(', '); }""")
        if error_text:
            print(f'Found error message: {error_text}')
        else:
            print('No error messages found on auth routes')
    except Exception as e:
        print(f'FINDING: auth route test exception: {e}')
