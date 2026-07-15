// Quick test to verify resolver behavior for /x, /x/, /x/index style routes

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

// Test cases for /x, /x/, /x/index style routes
const testCases = [
  { input: '/help', expected: ['/help', '/help/', '/help/index'] },
  { input: '/help/', expected: ['/help/', '/help', '/help/index'] },
  { input: '/help/index', expected: ['/help/index', '/help', '/help/', '/help/index'] },
  { input: '/ai-learning-hub', expected: ['/ai-learning-hub', '/ai-learning-hub/', '/ai-learning-hub/index'] },
  { input: '/ai-learning-hub/', expected: ['/ai-learning-hub/', '/ai-learning-hub', '/ai-learning-hub/index'] },
  { input: '/ai-learning-hub/index', expected: ['/ai-learning-hub/index', '/ai-learning-hub', '/ai-learning-hub/', '/ai-learning-hub/index'] },
  { input: '/', expected: ['/'] },
  { input: '/index', expected: ['/index', '/', '/index'] },
];

console.log('Testing getExactAliasCandidates resolver behavior:\n');

let allPassed = true;
testCases.forEach(({ input, expected }) => {
  const normalized = normalizePath(input).toLowerCase();
  const result = getExactAliasCandidates(normalized);
  
  // Check if all expected variants are present
  const hasAllExpected = expected.every(e => result.includes(e));
  const passed = hasAllExpected;
  
  console.log(`Input: "${input}"`);
  console.log(`  Normalized: "${normalized}"`);
  console.log(`  Result: [${result.map(r => `"${r}"`).join(', ')}]`);
  console.log(`  Expected: [${expected.map(e => `"${e}"`).join(', ')}]`);
  console.log(`  Status: ${passed ? '✅ PASS' : '❌ FAIL'}`);
  console.log('');
  
  if (!passed) allPassed = false;
});

console.log(`\nOverall: ${allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);

// Test that the resolver handles edge cases safely
console.log('\n--- Edge Case Safety Tests ---\n');

const edgeCases = [
  { input: '', expected: ['/'] },
  { input: '   ', expected: ['/'] },
  { input: 'no-slash', expected: ['/no-slash', '/no-slash/', '/no-slash/index'] },
  { input: '//', expected: ['/'] },
  { input: '///', expected: ['/'] },
];

edgeCases.forEach(({ input, expected }) => {
  const normalized = normalizePath(input).toLowerCase();
  const result = getExactAliasCandidates(normalized);
  
  const hasAllExpected = expected.every(e => result.includes(e));
  const passed = hasAllExpected;
  
  console.log(`Input: "${input}"`);
  console.log(`  Normalized: "${normalized}"`);
  console.log(`  Result: [${result.map(r => `"${r}"`).join(', ')}]`);
  console.log(`  Expected: [${expected.map(e => `"${e}"`).join(', ')}]`);
  console.log(`  Status: ${passed ? '✅ PASS' : '❌ FAIL'}`);
  console.log('');
  
  if (!passed) allPassed = false;
});

console.log(`\nFinal Result: ${allPassed ? '✅ ALL TESTS PASSED - Resolver is safe' : '❌ SOME TESTS FAILED'}`);
process.exit(allPassed ? 0 : 1);
