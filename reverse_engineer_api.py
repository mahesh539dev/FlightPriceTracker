"""
Reverse-engineer Google Flights API by intercepting network calls with Playwright.
This script will capture the POST request to FlightsFrontendService and save it.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def capture_api_calls():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False to see browser
        page = await browser.new_page()

        # Intercept and log all network requests
        captured_requests = []

        async def handle_request(request):
            if "FlightsFrontendService" in request.url or "/search" in request.url:
                print(f"\n=== CAPTURED REQUEST ===")
                print(f"URL: {request.url}")
                print(f"Method: {request.method}")
                print(f"Headers: {request.headers}")
                try:
                    post_data = request.post_data
                    print(f"Body (raw): {post_data[:500] if post_data else 'None'}")
                    if post_data:
                        captured_requests.append({
                            "url": request.url,
                            "method": request.method,
                            "headers": dict(request.headers),
                            "body": post_data
                        })
                except Exception as e:
                    print(f"Error reading body: {e}")

        page.on("request", handle_request)

        # Navigate to Google Flights with search params
        origin = "YYZ"
        destination = "BOM"
        date_from = "2026-06-01"

        url = f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{destination}+on+{date_from}"
        print(f"Navigating to: {url}")

        await page.goto(url, wait_until="networkidle", timeout=30000)

        # Wait for results
        try:
            await page.wait_for_selector('[data-testid="offer-listing"]', timeout=15000)
            print("\nResults loaded!")
        except Exception as e:
            print(f"Timeout waiting for results: {e}")

        # Save all captured requests
        if captured_requests:
            output_path = Path("api_captures.json")
            with open(output_path, "w") as f:
                json.dump(captured_requests, f, indent=2)
            print(f"\nSaved {len(captured_requests)} captured requests to {output_path}")

        # Also save the current page content
        html = await page.content()
        Path("captured_page.html").write_text(html)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_api_calls())
