# AI Parallel Coding - Dialogue Visualization Frontend

Real-time worker-orchestrator dialogue monitoring interface.

## 🚀 Quick Start

### Prerequisites

- Node.js >= 18.0.0
- Backend API running on `http://localhost:8000`

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The application will be available at `http://localhost:5173`.

## 🏗️ Architecture

```
┌──────────────┐     WebSocket      ┌──────────────┐
│   Frontend   │ ◄─────────────────► │   Backend    │
│  React + TS  │  ws://localhost:8000│  FastAPI     │
└──────────────┘                     └──────────────┘
       │                                     │
       │                                     │
       ▼                                     ▼
   Browser UI                        dialogue_transcript.jsonl
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── DialogueView.tsx    # Main dialogue container
│   │   ├── Message.tsx         # Individual message display
│   │   └── ConnectionStatus.tsx # Connection indicator
│   ├── hooks/               # Custom React hooks
│   │   └── useWebSocket.ts     # WebSocket connection manager
│   ├── types/               # TypeScript type definitions
│   │   └── dialogue.ts         # Dialogue-related types
│   ├── App.tsx              # Application entry point
│   ├── App.css
│   └── index.css            # Global styles (Tailwind)
├── public/                  # Static assets
├── tailwind.config.js       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
├── vite.config.ts           # Vite build configuration
└── package.json
```

## 🔧 Configuration

### Backend API URL

Edit `src/hooks/useWebSocket.ts` to change the default backend URL:

```typescript
const {
  baseUrl = 'ws://localhost:8000',  // Change this
  // ...
} = options;
```

### Worker ID

Edit `src/App.tsx` to change the monitored worker:

```typescript
const [workerId] = useState('worker_test_001');  // Change this
```

## 🎨 Features

### Real-time Dialogue Streaming

- **WebSocket Connection**: Auto-reconnecting WebSocket with exponential backoff
- **Message Display**: Color-coded messages (Worker=Blue, Orchestrator=Purple)
- **Auto-scroll**: Automatically scrolls to latest message
- **Status Indicator**: Visual connection status (disconnected/connecting/connected/error)

### UI Components

#### DialogueView

Main container that manages the entire dialogue interface.

**Props:**
- `workerId: string` - Worker identifier to monitor
- `className?: string` - Optional CSS classes

**Features:**
- Real-time message streaming
- Connection status display
- Loading states
- Error handling with retry

#### Message

Displays individual dialogue entries.

**Props:**
- `entry: DialogueEntry` - Dialogue entry data
- `className?: string` - Optional CSS classes

**Features:**
- Direction-based coloring
- Timestamp formatting (HH:MM:SS)
- Confirmation badges (bash, write_file, read_file)
- Hover effects

#### ConnectionStatus

Shows WebSocket connection status with visual indicators.

**Props:**
- `status: ConnectionStatus` - Current connection status
- `error: string | null` - Error message if any
- `onReconnect: () => void` - Reconnect callback

**Features:**
- 5 states: disconnected/connecting/connected/reconnecting/error
- Color-coded badges
- Animated indicators
- Reconnect button (on error)
- Error tooltips

### useWebSocket Hook

Custom hook for managing WebSocket connections.

**Usage:**

```typescript
const { messages, status, error, isReady, disconnect, reconnect } =
  useWebSocket('worker_001', {
    baseUrl: 'ws://localhost:8000',
    maxReconnectAttempts: Infinity,
    reconnectDelay: 1000,
    maxReconnectDelay: 30000,
    autoReconnect: true,
  });
```

**Features:**
- Automatic reconnection with exponential backoff
- Message buffering
- Type-safe message handling
- Connection status tracking
- Cleanup on unmount

## 🧪 Testing

```bash
# Run linter
npm run lint

# Type check
npm run build  # Runs tsc before build
```

## 📦 Build

```bash
# Production build
npm run build

# Output: dist/
#   ├── index.html
#   ├── assets/
#   │   ├── index-[hash].js   (~204 KB)
#   │   └── index-[hash].css  (~13 KB)
```

## 🎨 Styling

Uses **Tailwind CSS 3** for styling.

### Custom Colors

Defined in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      'worker': '#3b82f6',        // Blue for worker messages
      'orchestrator': '#8b5cf6',  // Purple for orchestrator messages
    }
  }
}
```

## 🐛 Troubleshooting

### WebSocket Connection Failed

**Problem:** Cannot connect to backend API

**Solutions:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS configuration in backend
3. Verify firewall settings

### Build Errors

**Problem:** TypeScript or build errors

**Solutions:**
1. Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf node_modules/.vite`
3. Check TypeScript version: `npx tsc --version`

### No Messages Displayed

**Problem:** Connected but no messages appear

**Solutions:**
1. Verify worker exists: `curl http://localhost:8000/api/v1/workers`
2. Check dialogue file exists: `workspace/worker_XXX/dialogue_transcript.jsonl`
3. Open browser console for errors

## 📊 Performance

- **Bundle Size**: 204 KB (gzipped: 64 KB)
- **CSS Size**: 13 KB (gzipped: 3 KB)
- **Build Time**: ~3 seconds
- **First Load**: < 1 second
- **WebSocket Latency**: < 100ms

## 🔐 Security

- No authentication (development only)
- CORS enabled for `localhost:3000`, `localhost:5173`, `localhost:8080`
- WebSocket connections from same origin only

**⚠️ Production deployment requires:**
- HTTPS/WSS
- Authentication
- Rate limiting
- Input validation

## 📝 License

Part of the AI_Investor ecosystem.

## 🤝 Contributing

This is a component of the parallel AI coding system. See main project README for contribution guidelines.

---

**Built with:** React 19 + TypeScript 5 + Vite 7 + Tailwind CSS 3
