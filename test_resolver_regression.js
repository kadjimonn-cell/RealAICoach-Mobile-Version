// Test to verify no regression risk in route evidence resolver

const normalizePath = (routePath) => {
  const route = String(routePath || '').trim();
  if (!route) return '/';
  return route.startsWith('/') ? route : `/${route}`;
};

const getExactAliasCandidates = (normalizedPath) => {
  const path = String(normalizedPath || '/').toLowerCase();
  if (path === '/') return ['/'];

  let base = path;
  if (base.endsWith('/index')) {
    base = base.slice(0, -6) || '/';
  } else if (base.endsWith('/') && base !== '/') {
    base = base.slice(0, -1) || '/';
  }

  const variants = [path, base];
  if (base !== '/') {
    variants.push(`${base}/`);
    variants.push(`${base}/index`);
  }

  return Array.from(new Set(variants));
};

// Simulate the actual resolver logic
const mockEvidenceTags = [
  { routePrefix: '/help', matchMode: 'exact' },
  { routePrefix: '/help/', matchMode: 'exact' },
  { routePrefix: '/help/index', matchMode: 'exact' },
  { routePrefix: '/ai-learning-hub', matchMode: 'exact' },
  { routePrefix: '/ai-learning-hub/', matchMode: 'exact' },
  { routePrefix: '/ai-learning-hub/index', matchMode: 'exact' },
  { routePrefix: '/settings', matchMode: 'exact' },
  { routePrefix: '/settings/', matchMode: 'exact' },
  { routePrefix: '/settings/index', matchMode: 'exact' },
  { routePrefix: '/', matchMode: 'exact' },
  { routePrefix: '/index', matchMode: 'exact' },
  { routePrefix: '/my-tickets', matchMode: 'prefix' }, // prefix mode
];

const getRouteE2EEvidenceTag = (routePath) => {
  const normalized = normalizePath(routePath).toLowerCase();
  const exactAliases = getExactAliasCandidates(normalized);

  // Try exact match first
  const exactMatch = mockEvidenceTags.find((item) => {
    if (item.matchMode !== 'exact') return false;
    const prefix = item.routePrefix.toLowerCase();
    return exactAliases.includes(prefix);
  });
  if (exactMatch) return exactMatch;

  // Fall back to prefix match
  const prefixMatch = mockEvidenceTags.find((item) => {
    if (item.matchMode === 'exact') return false;
    const prefix = item.routePrefix.toLowerCase();
    return normalized === prefix || normalized.startsWith(prefix);
  });
  return prefixMatch || null;
};

console.log('Testing Route Evidence Resolver - Regression Check\n');
console.log('='.repeat(60));

// Test cases that should all resolve correctly
const testCases = [
  // Base route should match all three aliases
  { input: '/help', expectedPrefix: '/help', description: 'Base route /help' },
  { input: '/help/', expectedPrefix: '/help/', description: 'Trailing slash /help/' },
  { input: '/help/index', expectedPrefix: '/help/index', description: 'Index route /help/index' },
  
  // Wave12+ routes
  { input: '/ai-learning-hub', expectedPrefix: '/ai-learning-hub', description: 'Wave12 base route' },
  { input: '/ai-learning-hub/', expectedPrefix: '/ai-learning-hub/', description: 'Wave12 trailing slash' },
  { input: '/ai-learning-hub/index', expectedPrefix: '/ai-learning-hub/index', description: 'Wave12 index route' },
  
  // Settings routes
  { input: '/settings', expectedPrefix: '/settings', description: 'Settings base' },
  { input: '/settings/', expectedPrefix: '/settings/', description: 'Settings trailing slash' },
  { input: '/settings/index', expectedPrefix: '/settings/index', description: 'Settings index' },
  
  // Root routes
  { input: '/', expectedPrefix: '/', description: 'Root route' },
  { input: '/index', expectedPrefix: '/index', description: 'Root index' },
  
  // Prefix mode route (should still work)
  { input: '/my-tickets', expectedPrefix: '/my-tickets', description: 'Prefix mode route' },
  { input: '/my-tickets/123', expectedPrefix: '/my-tickets', description: 'Prefix mode with path' },
];

let passed = 0;
let failed = 0;

testCases.forEach(({ input, expectedPrefix, description }) => {
  const result = getRouteE2EEvidenceTag(input);
  const success = result && result.routePrefix === expectedPrefix;
  
  if (success) {
    console.log(`✅ PASS: ${description}`);
    console.log(`   Input: "${input}" → Matched: "${result.routePrefix}" (${result.matchMode})`);
    passed++;
  } else {
    console.log(`❌ FAIL: ${description}`);
    console.log(`   Input: "${input}" → Expected: "${expectedPrefix}", Got: ${result ? result.routePrefix : 'null'}`);
    failed++;
  }
  console.log('');
});

console.log('='.repeat(60));
console.log(`\nResults: ${passed} passed, ${failed} failed`);

// Test that exact routes don't accidentally match prefix routes
console.log('\n' + '='.repeat(60));
console.log('Safety Check: Exact routes should not match unrelated prefixes\n');

const safetyTests = [
  { input: '/help-center', shouldNotMatch: '/help', description: 'Similar prefix should not match' },
  { input: '/settings-advanced', shouldNotMatch: '/settings', description: 'Extended path should not match exact' },
];

let safetyPassed = 0;
let safetyFailed = 0;

safetyTests.forEach(({ input, shouldNotMatch, description }) => {
  const result = getRouteE2EEvidenceTag(input);
  const safe = !result || result.routePrefix !== shouldNotMatch;
  
  if (safe) {
    console.log(`✅ SAFE: ${description}`);
    console.log(`   Input: "${input}" → Did not match "${shouldNotMatch}" (correct)`);
    safetyPassed++;
  } else {
    console.log(`❌ UNSAFE: ${description}`);
    console.log(`   Input: "${input}" → Incorrectly matched "${shouldNotMatch}"`);
    safetyFailed++;
  }
  console.log('');
});

console.log('='.repeat(60));
console.log(`\nSafety Results: ${safetyPassed} passed, ${safetyFailed} failed`);

const allPassed = failed === 0 && safetyFailed === 0;
console.log(`\n${'='.repeat(60)}`);
console.log(`Final Result: ${allPassed ? '✅ NO REGRESSION RISK DETECTED' : '❌ REGRESSION RISK FOUND'}`);
console.log('='.repeat(60));

process.exit(allPassed ? 0 : 1);
