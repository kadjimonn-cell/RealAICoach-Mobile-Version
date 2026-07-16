#!/usr/bin/env python3
"""
Welcome Page Responsive Test Suite
Tests viewport responsiveness across 9 breakpoints: 320, 360, 390, 430, 560, 768, 936, 1024, 1365
"""

import asyncio
from playwright.async_api import async_playwright

VIEWPORTS = [
    {"width": 320, "height": 844, "label": "320px (small phone)"},
    {"width": 360, "height": 844, "label": "360px (phone)"},
    {"width": 390, "height": 844, "label": "390px (iPhone 14)"},
    {"width": 430, "height": 844, "label": "430px (iPhone 14 Pro Max)"},
    {"width": 560, "height": 844, "label": "560px (large phone)"},
    {"width": 768, "height": 1024, "label": "768px (tablet)"},
    {"width": 936, "height": 1024, "label": "936px (tablet landscape)"},
    {"width": 1024, "height": 1024, "label": "1024px (small desktop)"},
    {"width": 1365, "height": 900, "label": "1365px (desktop)"},
]

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com/welcome"

async def test_viewport(page, vp):
    """Test a single viewport"""
    issues = []
    
    print(f"\n=== Testing {vp['label']} ===")
    await page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
    await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)
    
    # A) Check page loads
    welcome = await page.query_selector('[data-testid="welcome-screen"]')
    if welcome:
        print(f"  [PASS] Welcome screen loaded")
    else:
        issues.append("Welcome screen not found")
        print(f"  [FAIL] Welcome screen not found")
    
    # B) Check horizontal overflow
    overflow = await page.evaluate("() => document.body.scrollWidth > window.innerWidth")
    if overflow:
        body_w = await page.evaluate("() => document.body.scrollWidth")
        win_w = await page.evaluate("() => window.innerWidth")
        issues.append(f"Horizontal overflow: body={body_w}, window={win_w}")
        print(f"  [FAIL] Horizontal overflow: body={body_w}, window={win_w}")
    else:
        print(f"  [PASS] No horizontal overflow")
    
    # C) Check featured-in section
    featured = await page.query_selector('[data-testid="welcome-featured-in-marquee"]')
    if featured:
        box = await featured.bounding_box()
        if box and box["width"] > 0:
            print(f"  [PASS] Featured-in visible (w={box['width']:.0f})")
        else:
            issues.append("Featured-in zero width")
            print(f"  [FAIL] Featured-in zero width")
    else:
        print(f"  [INFO] Featured-in not found (may be deferred)")
    
    # D) Check featured-in chips
    chips = await page.query_selector_all('[data-testid^="welcome-featured-in-chip-"]')
    if len(chips) > 0:
        print(f"  [PASS] {len(chips)} featured-in chips visible")
    else:
        # May be deferred, not a critical failure
        print(f"  [INFO] No featured-in chips (may be deferred)")
    
    # E) Scroll to footer and check quick-nav overlap
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1500)
    
    # Check quick-nav suppression near footer
    quick_nav = await page.query_selector('[data-testid="welcome-mobile-quick-nav-drawer"]')
    if quick_nav:
        qn_box = await quick_nav.bounding_box()
        if qn_box:
            issues.append("Quick-nav visible near footer (overlap risk)")
            print(f"  [FAIL] Quick-nav visible near footer")
        else:
            print(f"  [PASS] Quick-nav suppressed near footer")
    else:
        print(f"  [PASS] No quick-nav overlap")
    
    return {"viewport": vp["label"], "width": vp["width"], "issues": issues}

async def main():
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        for vp in VIEWPORTS:
            result = await test_viewport(page, vp)
            results.append(result)
        
        await browser.close()
    
    # Summary
    print("\n" + "="*60)
    print("RESPONSIVE TEST SUMMARY")
    print("="*60)
    
    total_issues = 0
    for r in results:
        if r["issues"]:
            total_issues += len(r["issues"])
            print(f"\n{r['viewport']}: FAIL")
            for issue in r["issues"]:
                print(f"  - {issue}")
        else:
            print(f"{r['viewport']}: PASS")
    
    print(f"\n{'='*60}")
    print(f"Total viewports tested: {len(results)}")
    print(f"Total issues found: {total_issues}")
    if total_issues == 0:
        print("ALL RESPONSIVE TESTS PASSED!")
    print("="*60)
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
