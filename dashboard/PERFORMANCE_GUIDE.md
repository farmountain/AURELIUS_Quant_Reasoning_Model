"""
Frontend performance optimization guide
Strategies to improve React dashboard performance
"""

# Performance Optimizations Implemented:

## 1. Code Splitting & Lazy Loading
# Lazy load routes to reduce initial bundle size
# Example in App.jsx:
```javascript
import { lazy, Suspense } from 'react';

// Lazy load heavy components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Strategies = lazy(() => import('./pages/Strategies'));
const StrategyDetail = lazy(() => import('./pages/StrategyDetail'));
const Backtests = lazy(() => import('./pages/Backtests'));

// Wrap with Suspense
<Suspense fallback={<LoadingSpinner size="lg" />}>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/strategies" element={<Strategies />} />
    {/* ... */}
  </Routes>
</Suspense>
```

## 2. React.memo for Pure Components
# Memoize components that don't need frequent re-renders
```javascript
import { memo } from 'react';

const Header = memo(({ user, onLogout }) => {
  // Component code
});

export default Header;
```

## 3. useMemo for Expensive Calculations
```javascript
import { useMemo } from 'react';

const processedData = useMemo(() => {
  return heavyComputation(data);
}, [data]);
```

## 4. useCallback for Event Handlers
```javascript
import { useCallback } from 'react';

const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

## 5. Virtual Scrolling for Large Lists
# For strategy/backtest lists with 100+ items
```bash
npm install react-window
```

```javascript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={items.length}
  itemSize={80}
>
  {({ index, style }) => (
    <div style={style}>{items[index]}</div>
  )}
</FixedSizeList>
```

## 6. Image Optimization
# Use next-gen formats and lazy loading
```javascript
<img 
  src="chart.webp" 
  loading="lazy" 
  alt="Chart"
/>
```

## 7. Bundle Size Analysis
```bash
cd dashboard
npm run build
npm install -D rollup-plugin-visualizer
```

## 8. Service Worker for Caching
```bash
npm install workbox-cli
```

## 9. Debounce Search Inputs
```javascript
import { useMemo } from 'react';
import debounce from 'lodash.debounce';

const debouncedSearch = useMemo(
  () => debounce((value) => search(value), 300),
  []
);
```

## 10. Reduce Re-renders with Context Splitting
# Split large contexts into smaller, focused ones
```javascript
// Instead of one AuthContext with everything
// Split into UserContext and TokenContext
```
