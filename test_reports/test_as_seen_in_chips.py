#!/usr/bin/env python3
"""
Test script for verifying "As seen in" chips centering fix on Welcome page.
Tests responsive behavior across multiple viewport widths.
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com/welcome"

# Test viewports
TEST_VIEWPORTS = [
    {"width": 320, "height": 844, "name": "Mobile XS (320)"},
    {"width": 360, "height": 844, "name": "Mobile S (360)"},
    {"width": 390, "height": 844, "name": "Mobile M (390)"},
    {"width": 430, "height": 844, "name": "Mobile L (430)"},
    {"width": 768, "height": 1024, "name": "Tablet (768)"},
    {"width": 936, "height": 1024, "name": "Tablet L (936)"},
    {"width": 1024, "height": 1080, "name": "Desktop S (1024)"},
]

async def test_as_seen_in_chips():
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for vp in TEST_VIEWPORTS:
            context = await browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = await context.new_page()
            
            try:
                print(f"\n=== Testing viewport: {vp['name']} ===")
                
                await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(4000)
                
                # Wait for welcome screen
                try:
                    await page.wait_for_selector('[data-testid="welcome-screen"]', timeout=20000)
                    print(f"  Welcome screen loaded at {vp['width']}px")
                except:
                    print(f"  WARNING: Welcome screen selector not found, checking for content...")
                
                # Find the "As seen in" strip
                as_seen_strip = await page.query_selector('[data-testid="welcome-hero-as-seen-strip"]')
                if not as_seen_strip:
                    print(f"  ERROR: As seen in strip not found at {vp['width']}px")
                    results.append({"viewport": vp["name"], "width": vp["width"], "status": "FAIL", "reason": "Strip not found"})
                    await context.close()
                    continue
                
                print(f"  As seen in strip found")
                
                # Get chip container info using JavaScript
                chip_info = await page.evaluate("""() => {
                    const strip = document.querySelector('[data-testid="welcome-hero-as-seen-strip"]');
                    if (!strip) return null;
                    
                    // Find the chip container (div with flex-wrap)
                    const children = Array.from(strip.children);
                    const chipContainer = children.find(child => {
                        const style = window.getComputedStyle(child);
                        return style.flexWrap === 'wrap';
                    });
                    
                    if (!chipContainer) return { error: 'Chip container not found' };
                    
                    const containerStyle = window.getComputedStyle(chipContainer);
                    const chips = Array.from(chipContainer.querySelectorAll('[data-testid^="welcome-hero-as-seen-chip-"]'));
                    
                    const chipData = chips.map((chip, idx) => {
                        const style = window.getComputedStyle(chip);
                        const rect = chip.getBoundingClientRect();
                        return {
                            index: idx,
                            minWidth: style.minWidth,
                            textAlign: style.textAlign,
                            left: rect.left,
                            width: rect.width
                        };
                    });
                    
                    return {
                        justifyContent: containerStyle.justifyContent,
                        alignItems: containerStyle.alignItems,
                        alignContent: containerStyle.alignContent,
                        chipCount: chips.length,
                        chips: chipData,
                        hasOverflow: document.body.scrollWidth > window.innerWidth
                    };
                }""")
                
                if not chip_info or chip_info.get('error'):
                    print(f"  ERROR: {chip_info.get('error', 'Unknown error')}")
                    results.append({"viewport": vp["name"], "width": vp["width"], "status": "FAIL", "reason": chip_info.get('error', 'Unknown error')})
                    await context.close()
                    continue
                
                print(f"  justifyContent: {chip_info['justifyContent']}")
                print(f"  alignItems: {chip_info['alignItems']}")
                print(f"  alignContent: {chip_info['alignContent']}")
                print(f"  Chip count: {chip_info['chipCount']}")
                
                # Check centering
                is_centered = chip_info['justifyContent'] == 'center'
                
                # Check chip minWidth based on viewport
                expected_min_width = "132px" if vp["width"] < 430 else "144px"
                actual_min_widths = [c['minWidth'] for c in chip_info['chips']]
                min_width_correct = all(mw == expected_min_width for mw in actual_min_widths) if actual_min_widths else False
                
                # Check text alignment
                text_centered = all(c['textAlign'] == 'center' for c in chip_info['chips']) if chip_info['chips'] else False
                
                print(f"  Chips centered (justifyContent=center): {is_centered}")
                print(f"  Expected minWidth: {expected_min_width}, Actual: {actual_min_widths[0] if actual_min_widths else 'N/A'}")
                print(f"  minWidth correct: {min_width_correct}")
                print(f"  Text centered: {text_centered}")
                print(f"  Horizontal overflow: {chip_info['hasOverflow']}")
                
                # Determine status
                if is_centered and min_width_correct and text_centered and not chip_info['hasOverflow']:
                    status = "PASS"
                    reason = "All checks passed"
                else:
                    status = "FAIL"
                    reasons = []
                    if not is_centered:
                        reasons.append(f"Not centered (justifyContent={chip_info['justifyContent']})")
                    if not min_width_correct:
                        reasons.append(f"Wrong minWidth (expected {expected_min_width})")
                    if not text_centered:
                        reasons.append("Text not centered")
                    if chip_info['hasOverflow']:
                        reasons.append("Horizontal overflow")
                    reason = "; ".join(reasons)
                
                results.append({
                    "viewport": vp["name"],
                    "width": vp["width"],
                    "status": status,
                    "reason": reason,
                    "chipCount": chip_info['chipCount'],
                    "justifyContent": chip_info['justifyContent'],
                    "minWidth": actual_min_widths[0] if actual_min_widths else "N/A"
                })
                
                # Take screenshot for mobile viewports
                if vp["width"] <= 430:
                    await page.screenshot(path=f"/app/test_reports/as_seen_in_{vp['width']}.png")
                    print(f"  Screenshot saved: as_seen_in_{vp['width']}.png")
                
            except Exception as e:
                print(f"  ERROR at {vp['name']}: {str(e)}")
                results.append({"viewport": vp["name"], "width": vp["width"], "status": "ERROR", "reason": str(e)})
            
            await context.close()
        
        await browser.close()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY: As seen in Chips Centering Verification")
    print("="*60)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] in ["FAIL", "ERROR"])
    
    for r in results:
        status_icon = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"{status_icon} {r['viewport']}: {r['status']} - {r.get('reason', '')}")
        if r.get('chipCount'):
            print(f"    Chips: {r['chipCount']}, justifyContent: {r.get('justifyContent')}, minWidth: {r.get('minWidth')}")
    
    print(f"\nTotal: {passed}/{len(results)} passed")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_as_seen_in_chips())
