#!/usr/bin/env python3
"""
Test script for verifying "As seen in" chips centering fix on Welcome page.
Tests visual centering across multiple viewport widths.
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com/welcome"

TEST_VIEWPORTS = [
    {"width": 320, "height": 844, "name": "320px"},
    {"width": 360, "height": 844, "name": "360px"},
    {"width": 390, "height": 844, "name": "390px"},
    {"width": 430, "height": 844, "name": "430px"},
    {"width": 768, "height": 1024, "name": "768px"},
    {"width": 936, "height": 1024, "name": "936px"},
    {"width": 1024, "height": 1080, "name": "1024px"},
]

async def test_visual_centering():
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for vp in TEST_VIEWPORTS:
            context = await browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = await context.new_page()
            
            try:
                print(f"\n=== Testing {vp['name']} ===")
                
                await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(5000)
                
                try:
                    await page.wait_for_selector('[data-testid="welcome-screen"]', timeout=20000)
                    print(f"  Welcome screen loaded")
                except:
                    print(f"  WARNING: Welcome screen selector not found")
                
                # Check chip centering visually
                centering_info = await page.evaluate("""() => {
                    const strip = document.querySelector('[data-testid="welcome-hero-as-seen-strip"]');
                    if (!strip) return { error: 'Strip not found' };
                    
                    const stripRect = strip.getBoundingClientRect();
                    const children = Array.from(strip.children);
                    const chipContainer = children.find(child => {
                        const style = window.getComputedStyle(child);
                        return style.flexWrap === 'wrap';
                    });
                    
                    if (!chipContainer) return { error: 'Chip container not found' };
                    
                    const containerRect = chipContainer.getBoundingClientRect();
                    const containerStyle = window.getComputedStyle(chipContainer);
                    
                    const chips = Array.from(chipContainer.querySelectorAll('[data-testid^="welcome-hero-as-seen-chip-"]'));
                    
                    // Group chips by row
                    const rows = {};
                    chips.forEach(chip => {
                        const rect = chip.getBoundingClientRect();
                        const rowKey = Math.round(rect.top);
                        if (!rows[rowKey]) rows[rowKey] = [];
                        rows[rowKey].push({
                            left: rect.left,
                            right: rect.right,
                            width: rect.width,
                            text: chip.textContent
                        });
                    });
                    
                    // Calculate centering for each row
                    const rowAnalysis = Object.entries(rows).map(([top, rowChips]) => {
                        const leftmost = Math.min(...rowChips.map(c => c.left));
                        const rightmost = Math.max(...rowChips.map(c => c.right));
                        const leftMargin = leftmost - containerRect.left;
                        const rightMargin = containerRect.right - rightmost;
                        const marginDiff = Math.abs(leftMargin - rightMargin);
                        const isCentered = marginDiff < 20;
                        
                        return {
                            top: parseInt(top),
                            chipCount: rowChips.length,
                            leftMargin: Math.round(leftMargin),
                            rightMargin: Math.round(rightMargin),
                            marginDiff: Math.round(marginDiff),
                            isCentered,
                            chips: rowChips.map(c => c.text)
                        };
                    });
                    
                    return {
                        stripWidth: stripRect.width,
                        containerWidth: containerRect.width,
                        justifyContent: containerStyle.justifyContent,
                        chipCount: chips.length,
                        rowCount: Object.keys(rows).length,
                        rows: rowAnalysis,
                        allRowsCentered: rowAnalysis.every(r => r.isCentered),
                        hasOverflow: document.body.scrollWidth > window.innerWidth
                    };
                }""")
                
                if centering_info.get('error'):
                    print(f"  ERROR: {centering_info['error']}")
                    results.append({"viewport": vp["name"], "width": vp["width"], "status": "ERROR", "reason": centering_info['error']})
                    await context.close()
                    continue
                
                print(f"  Container width: {centering_info['containerWidth']:.0f}px")
                print(f"  justifyContent: {centering_info['justifyContent']}")
                print(f"  Chip count: {centering_info['chipCount']}")
                print(f"  Row count: {centering_info['rowCount']}")
                
                for row in centering_info['rows']:
                    centered_str = "CENTERED" if row['isCentered'] else "NOT CENTERED"
                    print(f"  Row: {row['chipCount']} chips, L={row['leftMargin']}px R={row['rightMargin']}px diff={row['marginDiff']}px [{centered_str}]")
                
                print(f"  All rows centered: {centering_info['allRowsCentered']}")
                print(f"  Horizontal overflow: {centering_info['hasOverflow']}")
                
                status = "PASS" if centering_info['allRowsCentered'] and not centering_info['hasOverflow'] else "FAIL"
                results.append({
                    "viewport": vp["name"],
                    "width": vp["width"],
                    "status": status,
                    "chipCount": centering_info['chipCount'],
                    "rowCount": centering_info['rowCount'],
                    "allRowsCentered": centering_info['allRowsCentered'],
                    "hasOverflow": centering_info['hasOverflow'],
                    "justifyContent": centering_info['justifyContent']
                })
                
                # Take screenshot for key viewports
                if vp["width"] in [320, 390, 768]:
                    await page.screenshot(path=f"/app/test_reports/chips_visual_{vp['width']}.png")
                    print(f"  Screenshot saved")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
                results.append({"viewport": vp["name"], "width": vp["width"], "status": "ERROR", "reason": str(e)})
            
            await context.close()
        
        await browser.close()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY: As Seen In Chips Visual Centering")
    print("="*60)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    for r in results:
        icon = "PASS" if r["status"] == "PASS" else "FAIL"
        details = f"{r.get('chipCount', 0)} chips, {r.get('rowCount', 0)} rows, centered={r.get('allRowsCentered', False)}, justifyContent={r.get('justifyContent', 'N/A')}"
        print(f"{icon} {r['viewport']}: {r['status']} - {details}")
    
    print(f"\nTotal: {passed}/{len(results)} passed")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_visual_centering())
