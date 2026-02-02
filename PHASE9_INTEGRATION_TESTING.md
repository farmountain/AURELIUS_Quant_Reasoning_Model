# Phase 9: Integration Testing - Setup & Execution Guide

**Date**: February 2, 2026  
**Status**: 🎯 IN PROGRESS  
**Duration**: 2-3 hours  
**Objective**: Full end-to-end system validation (API + Dashboard + WebSocket)

---

## 🎯 Phase 9 Objectives

Test the complete AURELIUS platform with all components working together:

✅ **Backend**: REST API with all 19 endpoints  
✅ **Frontend**: React dashboard with 8 pages  
✅ **Authentication**: JWT tokens with Bcrypt passwords  
✅ **Real-time**: WebSocket for live updates  
✅ **Database**: PostgreSQL persistence  

---

## 📋 Test Scenarios

### Scenario 1: User Authentication Flow
**Objective**: Verify registration, login, and token management

1. Register new user with valid email/password
2. Verify JWT token is returned
3. Login with registered credentials
4. Verify token is valid
5. Attempt login with wrong password (should fail)
6. Verify token expiration

### Scenario 2: Strategy Management
**Objective**: Test strategy creation and retrieval

1. Generate new strategies via API
2. List all strategies
3. Get specific strategy details
4. Verify strategy parameters
5. Validate strategy confidence scores

### Scenario 3: Backtest Execution
**Objective**: Test backtest workflow

1. Create strategy
2. Run backtest on strategy
3. Monitor backtest progress (via WebSocket)
4. Retrieve backtest results
5. Verify metrics calculations

### Scenario 4: Real-time Updates
**Objective**: Test WebSocket event streaming

1. Connect WebSocket with JWT token
2. Subscribe to events
3. Trigger strategy creation
4. Receive real-time notification
5. Verify message format

### Scenario 5: Dashboard Integration
**Objective**: Test frontend + backend communication

1. Load dashboard
2. Navigate to login page
3. Register new account
4. Login and access protected pages
5. Generate strategy (triggers real-time update)
6. Run backtest
7. View results

### Scenario 6: Error Handling
**Objective**: Verify proper error responses

1. Request without authentication
2. Invalid token
3. Non-existent resource
4. Invalid parameters
5. Server errors

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- All dependencies installed

### Step 1: Install Dependencies

**Backend**:
```bash
cd api
pip install -r requirements.txt
```

**Frontend**:
```bash
cd dashboard
npm install
```

### Step 2: Start the API Server

```bash
cd api
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Step 3: Start the Dashboard (New Terminal)

```bash
cd dashboard
npm run dev
```

Expected output:
```
VITE v5.0.0  ready in 234 ms

➜  Local:   http://localhost:3000/
```

### Step 4: Access the Application

**Dashboard**: http://localhost:3000/  
**API Docs**: http://localhost:8000/docs  
**API ReDoc**: http://localhost:8000/redoc  

---

## 🧪 Automated Integration Tests

### Run Python Test Suite

**Windows**:
```bash
cd api
python test_integration.py
```

**Linux/Mac**:
```bash
cd api
bash run_tests.sh
```

### Test Coverage

The `test_integration.py` script tests:

1. ✅ Health check endpoint
2. ✅ User registration
3. ✅ User login
4. ✅ Token verification
5. ✅ Strategy generation
6. ✅ Strategy listing
7. ✅ Backtest execution
8. ✅ WebSocket connection
9. ✅ Authentication required (negative test)
10. ✅ Invalid token rejection (negative test)

### Expected Output

```
============================================================
AURELIUS API Integration Test Suite
============================================================

✅ PASS: Health Check
  → Status: 200
✅ PASS: User Registration
  → User: test_1707000000@example.com, Token received: True
✅ PASS: User Login
  → User: login_test_1707000001@example.com, Token received: True
✅ PASS: Token Verification
  → Email verified: test_1707000000@example.com
✅ PASS: Strategy Generation
  → Generated 3 strategies
✅ PASS: List Strategies
  → Total strategies: 5
✅ PASS: Run Backtest
  → Backtest ID: 550e8400-e29b-41d4-a716-446655440000
✅ PASS: WebSocket Connection
  → Connected and received confirmation
✅ PASS: Authentication Required
  → Status: 401 (expected 401)
✅ PASS: Invalid Token Rejection
  → Status: 401 (expected 401/403)

============================================================
Test Results: 10 passed, 0 failed
============================================================
```

---

## 🌐 Manual Web-Based Testing

### 1. Register Account

**URL**: http://localhost:3000/register

**Steps**:
1. Enter email: `testuser@example.com`
2. Enter password: `TestPass123`
3. Confirm password: `TestPass123`
4. Click "Create Account"
5. Should redirect to dashboard

**Verify**:
- ✅ Account created in database
- ✅ Password hashed securely
- ✅ JWT token received

### 2. Login

**URL**: http://localhost:3000/login

**Steps**:
1. Enter email: `testuser@example.com`
2. Enter password: `TestPass123`
3. Click "Sign In"
4. Should redirect to dashboard

**Verify**:
- ✅ Token stored in localStorage
- ✅ User profile displayed in header
- ✅ All pages accessible

### 3. Generate Strategies

**URL**: http://localhost:3000/strategies

**Steps**:
1. Click "Generate Strategy" button
2. Enter market: "SPY"
3. Select timeframe: "1D"
4. Set risk: 0.5
5. Click "Generate"
6. Watch for new strategies to appear

**Verify**:
- ✅ Real-time update received (WebSocket)
- ✅ New strategies displayed
- ✅ Parameters shown correctly

### 4. Run Backtest

**URL**: http://localhost:3000/strategies

**Steps**:
1. Click on a strategy
2. Click "Run Backtest" button
3. Set parameters:
   - Start date: 2023-01-01
   - End date: 2023-12-31
   - Initial capital: 10000
   - Benchmark: SPY
4. Click "Execute Backtest"
5. Watch for results

**Verify**:
- ✅ Backtest starts (real-time event)
- ✅ Results appear when complete
- ✅ Metrics displayed correctly

### 5. Real-time Updates

**Expected Behavior**:
- When you generate a strategy in one tab, other tabs see the update immediately
- When a backtest completes, dashboard updates in real-time
- No page refresh needed

**Verify WebSocket in Browser**:
1. Open DevTools (F12)
2. Go to Network tab
3. Filter for "WS" (WebSocket)
4. Generate a strategy
5. Should see WebSocket messages

---

## 🔍 API Endpoint Testing (curl)

### 1. Health Check
```bash
curl http://127.0.0.1:8000/health
```

### 2. Register User
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "name": "Test User"
  }'
```

### 3. Login User
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'
```

### 4. Verify Token
```bash
curl -X GET http://127.0.0.1:8000/api/auth/verify \
  -H "Authorization: Bearer <TOKEN>"
```

### 5. Generate Strategies
```bash
curl -X POST http://127.0.0.1:8000/api/v1/strategies/generate \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Create momentum strategy",
    "risk_preference": "moderate",
    "max_strategies": 3
  }'
```

### 6. List Strategies
```bash
curl -X GET http://127.0.0.1:8000/api/v1/strategies/?skip=0&limit=10 \
  -H "Authorization: Bearer <TOKEN>"
```

### 7. Run Backtest
```bash
curl -X POST http://127.0.0.1:8000/api/v1/backtests/run \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "strategy-uuid",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 10000,
    "instruments": ["SPY"]
  }'
```

---

## ✅ Checklist

### API Testing
- [ ] Health endpoint responds
- [ ] Can register new user
- [ ] Can login with credentials
- [ ] Token verification works
- [ ] Can generate strategies
- [ ] Can list strategies
- [ ] Can run backtest
- [ ] WebSocket endpoint available
- [ ] Authentication required (401 without token)
- [ ] Invalid token rejected

### Dashboard Testing
- [ ] Can access login page
- [ ] Can register account
- [ ] Can login with credentials
- [ ] Dashboard loads after login
- [ ] All 8 pages accessible
- [ ] User profile shown in header
- [ ] Logout works
- [ ] Redirects to login when not authenticated

### Real-time Testing
- [ ] WebSocket connects successfully
- [ ] Receive connection confirmation
- [ ] Strategy creation events broadcast
- [ ] Backtest completion events broadcast
- [ ] Dashboard updates without refresh
- [ ] Multiple tabs receive updates simultaneously

### Error Handling
- [ ] Invalid credentials rejected
- [ ] Expired token rejected
- [ ] Missing authentication rejected
- [ ] Invalid parameters rejected
- [ ] Non-existent resources 404
- [ ] Server errors handled gracefully

---

## 🐛 Troubleshooting

### Issue: API won't start
**Solution**: 
```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Issue: Import errors in WebSocket
**Solution**: Already fixed in Phase 8. The function name is `verify_token`, not `verify_access_token`.

### Issue: Dashboard can't connect to API
**Solution**: Ensure API is running on http://127.0.0.1:8000 and check CORS configuration in `api/main.py`

### Issue: WebSocket connection fails
**Solution**: 
- Verify valid JWT token
- Check token in query string: `ws://localhost:8000/ws?token=<JWT>`
- Ensure websockets library installed: `pip install websockets`

### Issue: Database errors
**Solution**:
- Run migrations: `cd api && alembic upgrade head`
- Ensure PostgreSQL is running
- Check `DATABASE_URL` environment variable

### Issue: Slow testing
**Solution**: Reduce number of test iterations or skip optional tests. Tests should complete in < 30 seconds.

---

## 📊 Success Criteria

| Criterion | Status | Notes |
|-----------|--------|-------|
| All 19 API endpoints functional | 🎯 | 10+ tests coverage |
| Authentication working | 🎯 | JWT + Bcrypt |
| Database persistence | 🎯 | PostgreSQL |
| Real-time updates | 🎯 | WebSocket server |
| Dashboard responsive | 🎯 | React SPA |
| Error handling | 🎯 | 401, 404, validation |

---

## 📈 Next Steps After Testing

### If All Tests Pass ✅
1. Create summary report
2. Document any issues found
3. Move to Phase 10: Production Deployment
4. Create Docker containers
5. Deploy to cloud

### If Issues Found ❌
1. Document all failures
2. Create bug reports
3. Fix issues systematically
4. Re-run affected tests
5. Continue once all pass

---

## 📝 Test Report Template

```
AURELIUS Phase 9 Integration Test Report
========================================

Date: [Date]
Tester: [Name]
Environment: [OS/Python Version]

Test Results:
- Total Tests: 10
- Passed: 10
- Failed: 0
- Skipped: 0

Critical Issues: None
Major Issues: None
Minor Issues: None

Recommendations:
- System is production-ready
- All components functioning correctly
- No blocking issues identified

Signed: [Name]
Date: [Date]
```

---

## 🎓 Test Files Reference

| File | Purpose |
|------|---------|
| `api/test_integration.py` | Comprehensive Python test suite |
| `api/run_tests.sh` | Test runner for Linux/Mac |
| `api/run_tests.bat` | Test runner for Windows |

---

**Phase 9 Status**: 🎯 **IN PROGRESS**

Run `python test_integration.py` or `python run_tests.bat` to begin testing.

For detailed test output and troubleshooting, see this file or review individual test results.
