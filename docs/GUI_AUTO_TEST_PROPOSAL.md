# GUI Automated Testing System Proposal

**提案日**: 2025-10-24
**提案者**: User
**優先度**: 🟡 **中** (Quality Assurance)
**推定工数**: 1-2週間

---

## 🎯 Executive Summary

エコシステム全体のWeb GUIに対する自動テストシステムを構築し、スクリーンショット取得・自動操作・回帰テストを実現します。

---

## 📋 Overview

### Current Testing Gap

**現状**:
- ✅ Backend unit tests (29% coverage)
- ✅ API integration tests
- ✅ E2E tests (worker execution)
- ❌ **Frontend UI tests (0%)**  ← このギャップを埋める
- ❌ **Cross-browser tests (0%)**
- ❌ **Visual regression tests (0%)**

### Proposed Solution

**Playwright-based Automated Testing System**

```
┌────────────────────────────────────────────────┐
│  GUI Auto-Test Framework                       │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │ Test Scenarios                            │ │
│  │ • Login flow                              │ │
│  │ • Dashboard interaction                   │ │
│  │ • Worker Status monitoring                │ │
│  │ • Dialogue View                           │ │
│  │ • Terminal View                           │ │
│  │ • Metrics Dashboard                       │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │ Playwright Engine                         │ │
│  │ • Browser automation                      │ │
│  │ • Screenshot capture                      │ │
│  │ • Visual comparison                       │ │
│  │ • Performance measurement                 │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │ Test Reporting                            │ │
│  │ • HTML reports                            │ │
│  │ • Screenshot diffs                        │ │
│  │ • Performance metrics                     │ │
│  │ • CI/CD integration                       │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
         ↓ Tests
┌────────────────────────────────────────────────┐
│  Web GUIs                                       │
│  • Parallel Coding Dashboard (localhost:5173)  │
│  • Future MT4 Integration UI                   │
│  • Future Trading Dashboard                    │
│  • Any other ecosystem GUIs                    │
└────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Option 1: Playwright (推奨) ⭐

**理由**:
- ✅ Modern (Microsoft製、2020年～)
- ✅ 高速 (Seleniumより2-3倍高速)
- ✅ TypeScript完全対応
- ✅ 自動待機 (flaky test減少)
- ✅ スクリーンショット・動画録画標準装備
- ✅ Multi-browser (Chromium, Firefox, WebKit)
- ✅ Python + TypeScript両対応

**Installation**:
```bash
# Python
pip install playwright pytest-playwright
python -m playwright install

# TypeScript (recommended)
npm install -D @playwright/test
npx playwright install
```

### Option 2: Selenium

**理由**:
- ✅ 実績豊富 (2004年～)
- ✅ 大規模コミュニティ
- ⚠️ 遅い
- ⚠️ Flaky tests多い
- ⚠️ 手動待機が必要

### Recommendation: **Playwright** 🎯

---

## 📁 Proposed Structure

```
tools/parallel-coding/
├── tests/
│   ├── e2e/                          # ← NEW
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── test_dashboard_ui.py      # Dashboard tests
│   │   ├── test_worker_status.py     # Worker Status tests
│   │   ├── test_dialogue_view.py     # Dialogue View tests
│   │   ├── test_terminal_view.py     # Terminal View tests
│   │   ├── test_metrics_dashboard.py # Metrics tests
│   │   └── utils/
│   │       ├── page_objects.py       # Page Object Pattern
│   │       └── test_helpers.py       # Helper functions
│   │
│   └── visual/                       # ← NEW
│       ├── baseline/                 # Baseline screenshots
│       │   ├── dashboard.png
│       │   ├── worker-status.png
│       │   └── ...
│       └── diffs/                    # Visual diffs
│           └── ...
│
├── playwright.config.ts              # ← NEW (if using TypeScript)
├── pytest-playwright.ini             # ← NEW (if using Python)
│
└── docs/
    ├── GUI_AUTO_TEST_GUIDE.md        # ← NEW
    └── GUI_AUTO_TEST_PROPOSAL.md     # This file
```

---

## 🎬 Implementation Plan

### Phase 1: Setup & Infrastructure (Week 1) - 推定20時間

#### Task 1.1: Playwright Setup (2h)
```bash
# Install Playwright
cd tools/parallel-coding
npm install -D @playwright/test
npx playwright install

# Or Python
pip install playwright pytest-playwright
python -m playwright install
```

#### Task 1.2: Configuration (2h)

**playwright.config.ts**:
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

#### Task 1.3: Page Object Pattern Setup (4h)

**tests/e2e/utils/page_objects.py**:
```typescript
// tests/e2e/page-objects/DashboardPage.ts
import { Page, Locator } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly viewSelector: Locator;
  readonly workerStatusTab: Locator;
  readonly dialogueTab: Locator;
  readonly terminalTab: Locator;
  readonly metricsTab: Locator;

  constructor(page: Page) {
    this.page = page;
    this.viewSelector = page.locator('.view-selector');
    this.workerStatusTab = page.locator('button:has-text("Worker Status")');
    this.dialogueTab = page.locator('button:has-text("Dialogue")');
    this.terminalTab = page.locator('button:has-text("Terminal")');
    this.metricsTab = page.locator('button:has-text("Metrics")');
  }

  async goto() {
    await this.page.goto('/');
  }

  async switchToWorkerStatus() {
    await this.workerStatusTab.click();
    await this.page.waitForSelector('.worker-status-dashboard');
  }

  async switchToDialogue() {
    await this.dialogueTab.click();
    await this.page.waitForSelector('.dialogue-view');
  }

  async takeScreenshot(name: string) {
    await this.page.screenshot({
      path: `tests/visual/screenshots/${name}.png`,
      fullPage: true,
    });
  }
}
```

#### Task 1.4: First Test Implementation (4h)

**tests/e2e/test_dashboard_ui.py**:
```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';
import { DashboardPage } from './page-objects/DashboardPage';

test.describe('Dashboard UI Tests', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
  });

  test('should load dashboard successfully', async ({ page }) => {
    await expect(page).toHaveTitle(/Parallel Coding Dashboard/);
    await expect(dashboardPage.viewSelector).toBeVisible();
  });

  test('should switch between view modes', async ({ page }) => {
    // Worker Status
    await dashboardPage.switchToWorkerStatus();
    await expect(page.locator('.worker-status-dashboard')).toBeVisible();

    // Dialogue
    await dashboardPage.switchToDialogue();
    await expect(page.locator('.dialogue-view')).toBeVisible();

    // Terminal
    await dashboardPage.terminalTab.click();
    await expect(page.locator('.terminal-grid')).toBeVisible();

    // Metrics
    await dashboardPage.metricsTab.click();
    await expect(page.locator('.metrics-dashboard')).toBeVisible();
  });

  test('should capture screenshot of each view', async ({ page }) => {
    await dashboardPage.switchToWorkerStatus();
    await dashboardPage.takeScreenshot('worker-status');

    await dashboardPage.switchToDialogue();
    await dashboardPage.takeScreenshot('dialogue-view');
  });
});
```

#### Task 1.5: CI/CD Integration (4h)

**GitHub Actions Workflow**:
```yaml
# .github/workflows/gui-tests.yml
name: GUI Tests

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd tools/parallel-coding
          npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run GUI tests
        run: npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/

      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: screenshots
          path: tests/visual/screenshots/
```

#### Task 1.6: Documentation (4h)

Create `docs/GUI_AUTO_TEST_GUIDE.md`

---

### Phase 2: Core Test Suite (Week 2) - 推定30時間

#### Test Coverage Plan

**Priority 1: Critical User Flows (12h)**
```typescript
// tests/e2e/critical-flows.spec.ts

test('User can monitor worker execution', async ({ page }) => {
  // 1. Open dashboard
  // 2. Start worker execution
  // 3. Switch to Worker Status view
  // 4. Verify real-time updates
  // 5. Check worker completion
});

test('User can view AI dialogue', async ({ page }) => {
  // 1. Select worker from dropdown
  // 2. View dialogue messages
  // 3. Verify message formatting
  // 4. Test auto-scroll
});

test('User can search terminal output', async ({ page }) => {
  // 1. Open Terminal View
  // 2. Enter search query
  // 3. Verify highlighting
  // 4. Navigate with Next/Previous
});
```

**Priority 2: Component Tests (10h)**
- Worker Status Card tests
- Metrics Dashboard tests
- Connection Status tests
- Search functionality tests

**Priority 3: Visual Regression (8h)**
- Baseline screenshot capture
- Pixel-perfect comparison
- Responsive design tests (mobile/tablet/desktop)

---

### Phase 3: Advanced Features (Optional) - 推定15時間

#### Feature 1: Visual Regression Testing (6h)
```typescript
import { test, expect } from '@playwright/test';
import { toMatchImageSnapshot } from 'jest-image-snapshot';

test('visual regression - dashboard', async ({ page }) => {
  await page.goto('/');
  const screenshot = await page.screenshot();
  expect(screenshot).toMatchImageSnapshot({
    threshold: 0.01, // 1% difference allowed
    customSnapshotsDir: 'tests/visual/baseline',
  });
});
```

#### Feature 2: Performance Testing (5h)
```typescript
import { test, expect } from '@playwright/test';

test('performance - page load time', async ({ page }) => {
  const startTime = Date.now();
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  const loadTime = Date.now() - startTime;

  expect(loadTime).toBeLessThan(3000); // 3 seconds max
});

test('performance - WebSocket latency', async ({ page }) => {
  await page.goto('/');

  const latencies: number[] = [];
  page.on('websocket', ws => {
    ws.on('framesent', frame => {
      const start = Date.now();
      ws.on('framereceived', () => {
        latencies.push(Date.now() - start);
      });
    });
  });

  // Trigger some WebSocket activity
  await page.locator('.worker-status-tab').click();
  await page.waitForTimeout(5000);

  const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
  expect(avgLatency).toBeLessThan(100); // 100ms max
});
```

#### Feature 3: Accessibility Testing (4h)
```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('accessibility - dashboard', async ({ page }) => {
  await page.goto('/');

  const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

  expect(accessibilityScanResults.violations).toEqual([]);
});
```

---

## 🎯 Test Scenarios

### Scenario 1: Worker Execution Monitoring

**Steps**:
1. Open dashboard (localhost:5173)
2. Start worker execution (via API or UI)
3. Switch to Worker Status view
4. Verify worker card appears
5. Check status updates in real-time
6. Verify progress bar updates
7. Check completion notification

**Expected Results**:
- Worker appears within 2 seconds
- Status updates every 2 seconds
- Progress bar shows 0% → 100%
- Completion badge displays

### Scenario 2: Dialogue View Real-time Updates

**Steps**:
1. Open Dialogue View
2. Select active worker
3. Monitor dialogue messages
4. Verify timestamps
5. Check auto-scroll behavior

**Expected Results**:
- Messages appear within 1 second
- Timestamps are accurate
- Auto-scroll works smoothly
- Message formatting is correct

### Scenario 3: Terminal Search Functionality

**Steps**:
1. Open Terminal View
2. Wait for terminal output
3. Enter search query "error"
4. Verify highlighting
5. Click "Next" button
6. Verify navigation
7. Clear search

**Expected Results**:
- Matches highlighted in yellow
- Next/Previous navigation works
- Case-sensitive option works
- Regex option works

### Scenario 4: Visual Regression

**Steps**:
1. Capture baseline screenshots (once)
2. Run tests after code changes
3. Compare screenshots pixel-by-pixel
4. Flag differences > 1%

**Expected Results**:
- No unexpected visual changes
- Intentional changes are approved
- Regression report generated

---

## 📊 Success Metrics

### Test Coverage Goals

| Component | Target Coverage | Current | Gap |
|-----------|-----------------|---------|-----|
| **Frontend UI** | 80% | 0% | 80% |
| **Critical Flows** | 100% | 0% | 100% |
| **Visual Regression** | Key pages | 0% | 100% |
| **Performance** | All pages | 0% | 100% |
| **Accessibility** | WCAG AA | 0% | 100% |

### Quality Metrics

- **Test Execution Time**: < 5 minutes (full suite)
- **Flakiness Rate**: < 5%
- **Bug Detection Rate**: 90%+
- **False Positive Rate**: < 10%

---

## 🔧 Maintenance

### Regular Tasks

**Weekly**:
- Review test results
- Update baseline screenshots (if needed)
- Fix flaky tests

**Monthly**:
- Update Playwright version
- Review test coverage
- Add new test scenarios

**Quarterly**:
- Performance baseline review
- Accessibility audit
- Cross-browser compatibility check

---

## 💰 Cost-Benefit Analysis

### Costs

**Initial Setup**:
- Development time: 65 hours (1.5週間)
- Learning curve: 8 hours
- CI/CD setup: 4 hours
- **Total**: 77 hours

**Ongoing Maintenance**:
- Weekly: 2 hours
- Monthly: 4 hours
- Quarterly: 8 hours
- **Annual**: ~140 hours

### Benefits

**Bug Prevention**:
- Catch UI regressions before production
- Prevent breaking changes
- **Estimated bugs prevented**: 20-30/year

**Time Savings**:
- Reduce manual testing: -80%
- Faster releases: +50%
- **Annual time saved**: ~200 hours

**Quality Improvements**:
- Consistent UI quality
- Better user experience
- Higher confidence in releases

**ROI**: ~2.5x (200 saved / 77 invested)

---

## 🚦 Implementation Roadmap

### Week 1: Foundation
- [x] Technology decision (Playwright)
- [ ] Setup & configuration (2h)
- [ ] Page Object Pattern (4h)
- [ ] First test implementation (4h)
- [ ] CI/CD integration (4h)
- [ ] Documentation (4h)

**Deliverable**: Working GUI test infrastructure

### Week 2: Core Tests
- [ ] Critical user flow tests (12h)
- [ ] Component tests (10h)
- [ ] Visual regression baseline (8h)

**Deliverable**: Comprehensive test suite

### Week 3 (Optional): Advanced
- [ ] Performance tests (5h)
- [ ] Accessibility tests (4h)
- [ ] Cross-browser tests (6h)

**Deliverable**: Production-grade testing system

---

## 📚 Resources

### Documentation
- [Playwright Official Docs](https://playwright.dev/)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Page Object Model](https://playwright.dev/docs/pom)

### Tools
- [Playwright](https://playwright.dev/)
- [pytest-playwright](https://playwright.dev/python/docs/intro)
- [Axe Accessibility](https://github.com/dequelabs/axe-core)
- [Percy Visual Testing](https://percy.io/)

### Examples
- [Playwright Examples](https://github.com/microsoft/playwright/tree/main/examples)
- [E2E Testing Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)

---

## 🎯 Next Steps

### Immediate Actions

1. **User Decision**:
   - Approve implementation?
   - Priority level? (Phase 2 or Phase 3)
   - Scope? (MVP or Full)

2. **If Approved**:
   - Install Playwright
   - Create test structure
   - Implement first test
   - Run and validate

3. **Timeline**:
   - Week 1: Setup + Foundation
   - Week 2: Core test suite
   - Week 3: Advanced features (optional)

---

## 💬 Discussion Points

### Questions for User

1. **Priority**: Phase 2 or Phase 3?
   - Phase 2: Parallel with Manager AI (higher priority)
   - Phase 3: After Manager AI (lower priority)

2. **Scope**: What to test first?
   - Option A: Critical flows only (1 week)
   - Option B: Full coverage (2 weeks)
   - Option C: With advanced features (3 weeks)

3. **Tools**: Playwright or Selenium?
   - Recommendation: **Playwright** ✅

4. **Language**: TypeScript or Python?
   - TypeScript: Better Playwright integration
   - Python: Consistent with backend
   - Recommendation: **TypeScript** for E2E, Python for API tests

---

## 🎉 Conclusion

GUI自動テストシステムは、**エコシステムの品質保証に不可欠**です。

**Playwrightを使用することで**:
- ✅ Modern & fast testing
- ✅ Screenshot & video recording
- ✅ Visual regression detection
- ✅ Cross-browser compatibility
- ✅ CI/CD integration

**推奨**: Phase 2の一部として、まずMVP (1週間) を実装し、その後段階的に拡張。

---

**提案者**: User
**分析**: Claude (Sonnet 4.5)
**作成日**: 2025-10-24
**ステータス**: 📋 **Awaiting User Decision**

**Ready to ensure GUI quality with automated testing? 🧪**
