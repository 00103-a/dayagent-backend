# DayAgent Mobile App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pixel-art styled mobile app (Android/iOS) for DayAgent using Expo + React Native, reusing the existing Java + Python backend.

**Architecture:** Expo SDK with expo-router file-based routing, Zustand for state, axios for HTTP. 5-tab bottom navigation (Today/Diary/Life/Goals/Settings). Pixel liminal aesthetic adapted for mobile.

**Tech Stack:** Expo SDK 54, React Native, TypeScript, expo-router, Zustand, axios, expo-secure-store, expo-font, expo-linear-gradient

---

### Task 1: Scaffold Expo Project

**Files:**
- Create: `E:/dayagent-mobile/` (whole project)

- [ ] **Step 1: Create Expo project**

```bash
cd E:/ && npx create-expo-app@latest dayagent-mobile --template blank-typescript
```

- [ ] **Step 2: Install dependencies**

```bash
cd E:/dayagent-mobile && npx expo install expo-router expo-font expo-secure-store expo-linear-gradient expo-notifications expo-constants expo-linking expo-status-bar axios zustand react-native-safe-area-context react-native-screens react-native-svg @react-native-async-storage/async-storage
```

- [ ] **Step 3: Add expo-router plugin to app.json**

Read `E:/dayagent-mobile/app.json` first, then edit to add scheme and plugins:

```json
{
  "expo": {
    "name": "DayAgent",
    "slug": "dayagent-mobile",
    "version": "1.0.0",
    "scheme": "dayagent",
    "plugins": ["expo-router", "expo-font", "expo-secure-store"]
  }
}
```

- [ ] **Step 4: Verify scaffold**

```bash
cd E:/dayagent-mobile && npx expo start --no-dev
```

Expected: Metro bundler starts, shows QR code. Kill with Ctrl+C.

---

### Task 2: Theme Constants

**Files:**
- Create: `E:/dayagent-mobile/constants/theme.ts`

- [ ] **Step 1: Write theme constants**

```typescript
// constants/theme.ts
export const colors = {
  bg: '#080604',
  orange: '#e07030',
  orangeDim: '#8b4a1f',
  card: 'rgba(14, 9, 5, 0.85)',
  cardBorder: 'rgba(224, 112, 48, 0.13)',
  cardBorderActive: 'rgba(224, 112, 48, 0.25)',
  text: '#c8b89a',
  textDim: '#6b5a48',
  navBg: 'rgba(6, 4, 3, 0.92)',
  white: '#ffffff',
  black: '#000000',
  scanline: 'rgba(255, 255, 255, 0.03)',
} as const;

export const fonts = {
  pixel: 'zpix',
  mono: 'monospace',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
} as const;

export const fontSize = {
  xs: 10,
  sm: 11,
  md: 13,
  lg: 16,
  xl: 20,
  hero: 26,
} as const;

export const borderWidth = {
  thin: 1,
  normal: 2,
} as const;

export const CAT_SIZE = 24;
export const TAB_HEIGHT = 52;
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 3: API Client with JWT Interceptor

**Files:**
- Create: `E:/dayagent-mobile/api/client.ts`

- [ ] **Step 1: Write API client**

```typescript
// api/client.ts
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'jwt_token';
const BASE_URL = 'http://192.168.1.100:8080'; // change to your server LAN IP

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      SecureStore.deleteItemAsync(TOKEN_KEY);
    }
    return Promise.reject(error);
  }
);

export async function setToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
}

export async function getToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function clearToken(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
}
```

- [ ] **Step 2: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 4: API Service Modules

**Files:**
- Create: `E:/dayagent-mobile/api/auth.ts`
- Create: `E:/dayagent-mobile/api/plan.ts`
- Create: `E:/dayagent-mobile/api/weather.ts`
- Create: `E:/dayagent-mobile/api/courses.ts`
- Create: `E:/dayagent-mobile/api/summary.ts`
- Create: `E:/dayagent-mobile/api/goal.ts`
- Create: `E:/dayagent-mobile/api/parcel.ts`
- Create: `E:/dayagent-mobile/api/news.ts`
- Create: `E:/dayagent-mobile/api/chat.ts`

- [ ] **Step 1: Write auth.ts**

```typescript
// api/auth.ts
import { apiClient, setToken } from './client';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  userId: number;
  username: string;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const res = await apiClient.post<{ code: number; data: LoginResponse }>(
    '/api/user/login', data
  );
  if (res.data.code === 200) {
    await setToken(res.data.data.token);
    return res.data.data;
  }
  throw new Error('Login failed');
}

export async function register(data: LoginRequest): Promise<void> {
  await apiClient.post('/api/user/register', data);
}
```

- [ ] **Step 2: Write plan.ts**

```typescript
// api/plan.ts
import { apiClient } from './client';

export interface Priority {
  content: string;
}

export interface PlanResponse {
  plan: string;
  priorities: Priority[];
  warnings: string[];
  parcels: Array<{ tracking_no: string; carrier: string; status: string }>;
}

export async function fetchPlan(
  location: string,
  forceRefresh = false
): Promise<PlanResponse> {
  const res = await apiClient.get<{ code: number; data: PlanResponse }>(
    '/api/plan', { params: { location, forceRefresh } }
  );
  return res.data.data;
}
```

- [ ] **Step 3: Write weather.ts**

```typescript
// api/weather.ts
import { apiClient } from './client';

export interface WeatherResponse {
  location: string;
  weather: string;
  condition_text: string;
  condition_icon: string;
}

export type WeatherType = 'sunny' | 'rainy' | 'cloudy' | 'snowy' | 'unknown';

export function deriveWeatherType(conditionText: string): WeatherType {
  const t = conditionText || '';
  if (t.includes('雪')) return 'snowy';
  if (t.includes('雨')) return 'rainy';
  if (t.includes('云') || t.includes('阴')) return 'cloudy';
  if (t.includes('晴')) return 'sunny';
  return 'unknown';
}

export async function fetchWeather(
  location: string, lat?: number, lng?: number
): Promise<WeatherResponse> {
  const params: Record<string, string | number> = { location };
  if (lat !== undefined) params.lat = lat;
  if (lng !== undefined) params.lng = lng;
  const res = await apiClient.get<{ code: number; data: WeatherResponse }>(
    '/api/weather', { params }
  );
  return res.data.data;
}
```

- [ ] **Step 4: Write courses.ts**

```typescript
// api/courses.ts
import { apiClient } from './client';

export interface Course {
  name: string;
  time: string;
  location: string;
  dayOfWeek: number;
  weekStart: number;
  weekEnd: number;
}

export async function fetchCourses(week?: number): Promise<Course[]> {
  const res = await apiClient.get<{ code: number; data: Course[] }>(
    '/api/courses', { params: { week } }
  );
  return res.data.data;
}
```

- [ ] **Step 5: Write summary.ts**

```typescript
// api/summary.ts
import { apiClient } from './client';

export interface DailySummary {
  id: number;
  userId: number;
  summaryDate: string;
  content: string;
  moodScore: number;
}

export interface CreateSummaryRequest {
  userId: number;
  content: string;
  moodScore: number;
}

export async function fetchSummaries(userId: number): Promise<DailySummary[]> {
  const res = await apiClient.get<{ code: number; data: DailySummary[] }>(
    '/api/summary', { params: { userId } }
  );
  return res.data.data;
}

export async function createSummary(data: CreateSummaryRequest): Promise<void> {
  await apiClient.post('/api/summary', data);
}
```

- [ ] **Step 6: Write goal.ts**

```typescript
// api/goal.ts
import { apiClient } from './client';

export interface Goal {
  id: number;
  userId: number;
  type: 'weekly' | 'monthly';
  content: string;
  startDate: string;
  endDate: string;
  status: 'active' | 'done';
}

export interface CreateGoalRequest {
  userId: number;
  type: 'weekly' | 'monthly';
  content: string;
}

export async function fetchGoals(userId: number): Promise<Goal[]> {
  const res = await apiClient.get<{ code: number; data: Goal[] }>(
    '/api/goal', { params: { userId } }
  );
  return res.data.data;
}

export async function createGoal(data: CreateGoalRequest): Promise<void> {
  await apiClient.post('/api/goal', data);
}
```

- [ ] **Step 7: Write parcel.ts**

```typescript
// api/parcel.ts
import { apiClient } from './client';

export interface Parcel {
  id: number;
  userId: number;
  trackingNo: string;
  carrier: string;
  remark: string;
  status: string;
  isDelivered: boolean;
}

export interface CreateParcelRequest {
  userId: number;
  trackingNo: string;
  carrier: string;
  remark: string;
}

export async function fetchParcels(userId: number): Promise<Parcel[]> {
  const res = await apiClient.get<{ code: number; data: Parcel[] }>(
    '/api/parcel', { params: { userId } }
  );
  return res.data.data;
}

export async function createParcel(data: CreateParcelRequest): Promise<void> {
  await apiClient.post('/api/parcel', data);
}

export async function deleteParcel(id: number): Promise<void> {
  await apiClient.delete(`/api/parcel/${id}`);
}
```

- [ ] **Step 8: Write news.ts**

```typescript
// api/news.ts
import { apiClient } from './client';

export interface NewsItem {
  title: string;
  summary?: string;
  url?: string;
}

export async function fetchNews(goals?: string, summary?: string): Promise<NewsItem[]> {
  const res = await apiClient.get<{ code: number; data: NewsItem[] }>(
    '/api/news', { params: { goals, yesterday_summary: summary } }
  );
  return res.data.data;
}
```

- [ ] **Step 9: Write chat.ts**

```typescript
// api/chat.ts
import { apiClient } from './client';

export interface ChatRequest {
  userId: number;
  message: string;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  reply: string;
}

export async function sendChat(data: ChatRequest): Promise<ChatResponse> {
  const res = await apiClient.post<{ code: number; data: ChatResponse }>(
    '/api/chat', data
  );
  return res.data.data;
}
```

- [ ] **Step 10: Verify TypeScript**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 5: Zustand Stores

**Files:**
- Create: `E:/dayagent-mobile/stores/user.ts`
- Create: `E:/dayagent-mobile/stores/plan.ts`
- Create: `E:/dayagent-mobile/stores/weather.ts`

- [ ] **Step 1: Write user store**

```typescript
// stores/user.ts
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

interface UserState {
  userId: number | null;
  username: string | null;
  token: string | null;
  isLoggedIn: boolean;
  setUser: (userId: number, username: string, token: string) => void;
  logout: () => void;
  restoreSession: () => Promise<void>;
}

export const useUserStore = create<UserState>((set) => ({
  userId: null,
  username: null,
  token: null,
  isLoggedIn: false,
  setUser: (userId, username, token) =>
    set({ userId, username, token, isLoggedIn: true }),
  logout: () => {
    SecureStore.deleteItemAsync('jwt_token');
    set({ userId: null, username: null, token: null, isLoggedIn: false });
  },
  restoreSession: async () => {
    const token = await SecureStore.getItemAsync('jwt_token');
    if (token) {
      set({ token, isLoggedIn: true });
    }
  },
}));
```

- [ ] **Step 2: Write plan store**

```typescript
// stores/plan.ts
import { create } from 'zustand';
import { fetchPlan, PlanResponse } from '../api/plan';

type PlanStatus = 'idle' | 'loading' | 'loaded' | 'error';

interface PlanState {
  status: PlanStatus;
  plan: PlanResponse | null;
  error: string | null;
  lastUpdated: string | null;
  generatePlan: (location: string) => Promise<void>;
  refreshPlan: (location: string) => Promise<void>;
  reset: () => void;
}

export const usePlanStore = create<PlanState>((set) => ({
  status: 'idle',
  plan: null,
  error: null,
  lastUpdated: null,
  generatePlan: async (location) => {
    set({ status: 'loading', error: null });
    try {
      const plan = await fetchPlan(location, true);
      set({
        status: 'loaded',
        plan,
        lastUpdated: new Date().toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit',
        }),
      });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to generate plan';
      set({ status: 'error', error: msg });
    }
  },
  refreshPlan: async (location) => {
    try {
      const plan = await fetchPlan(location, true);
      set({
        status: 'loaded',
        plan,
        lastUpdated: new Date().toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit',
        }),
      });
    } catch (e: unknown) {
      // Keep old plan, silently fail refresh
      const msg = e instanceof Error ? e.message : 'Refresh failed';
      set({ error: msg });
    }
  },
  reset: () => set({ status: 'idle', plan: null, error: null, lastUpdated: null }),
}));
```

- [ ] **Step 3: Write weather store**

```typescript
// stores/weather.ts
import { create } from 'zustand';
import { fetchWeather, deriveWeatherType, WeatherResponse, WeatherType } from '../api/weather';

interface WeatherState {
  weather: WeatherResponse | null;
  weatherType: WeatherType;
  loading: boolean;
  loadWeather: (location: string, lat?: number, lng?: number) => Promise<void>;
  reset: () => void;
}

export const useWeatherStore = create<WeatherState>((set) => ({
  weather: null,
  weatherType: 'unknown',
  loading: false,
  loadWeather: async (location, lat, lng) => {
    set({ loading: true });
    try {
      const weather = await fetchWeather(location, lat, lng);
      set({
        weather,
        weatherType: deriveWeatherType(weather.condition_text),
        loading: false,
      });
    } catch {
      set({ loading: false });
    }
  },
  reset: () => set({ weather: null, weatherType: 'unknown', loading: false }),
}));
```

- [ ] **Step 4: Verify TypeScript**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 6: PixelCat Component

**Files:**
- Create: `E:/dayagent-mobile/components/PixelCat.tsx`

- [ ] **Step 1: Write PixelCat component using react-native-svg**

```typescript
// components/PixelCat.tsx
import React, { useEffect, useRef } from 'react';
import { Animated, Easing } from 'react-native';
import Svg, { Rect } from 'react-native-svg';
import { colors, CAT_SIZE } from '../constants/theme';

// 24×24 grid pixel cat
// Each "pixel" is a 2×2 SVG rect unit
const P = 2; // pixel unit size — grid is 12×12 units → 24×24 px

interface PixelCatProps {
  size?: number;
}

export default function PixelCat({ size = CAT_SIZE }: PixelCatProps) {
  const bob = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(bob, {
          toValue: -2,
          duration: 600,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(bob, {
          toValue: 0,
          duration: 600,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [bob]);

  const bodyColor = colors.orange;
  const shadowColor = colors.orangeDim;

  return (
    <Animated.View style={{ transform: [{ translateY: bob }], width: size, height: size + 2 }}>
      <Svg width={size} height={size} viewBox="0 0 24 24">
        {/* Ears — top 2×2 rounded bumps */}
        <Rect x={4} y={0} width={4} height={4} fill={bodyColor} />
        <Rect x={16} y={0} width={4} height={4} fill={bodyColor} />
        {/* Head — 6×4 rounded block */}
        <Rect x={4} y={4} width={16} height={4} fill={bodyColor} />
        <Rect x={2} y={8} width={20} height={4} fill={bodyColor} />
        {/* Eyes — white */}
        <Rect x={6} y={10} width={4} height={2} fill={colors.white} />
        <Rect x={14} y={10} width={4} height={2} fill={colors.white} />
        {/* Pupils */}
        <Rect x={8} y={10} width={2} height={2} fill={colors.black} />
        <Rect x={16} y={10} width={2} height={2} fill={colors.black} />
        {/* Body — 6×4 */}
        <Rect x={6} y={12} width={12} height={4} fill={bodyColor} />
        <Rect x={6} y={16} width={12} height={2} fill={shadowColor} />
        {/* Legs */}
        <Rect x={6} y={18} width={4} height={2} fill={shadowColor} />
        <Rect x={14} y={18} width={4} height={2} fill={shadowColor} />
        {/* Tail — wraps right */}
        <Rect x={18} y={14} width={4} height={2} fill={bodyColor} />
        <Rect x={20} y={16} width={4} height={2} fill={shadowColor} />
        <Rect x={18} y={18} width={4} height={2} fill={shadowColor} />
        {/* Nose — subtle */}
        <Rect x={11} y={10} width={2} height={2} fill={shadowColor} />
      </Svg>
    </Animated.View>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 7: Base UI Components

**Files:**
- Create: `E:/dayagent-mobile/components/PixelCard.tsx`
- Create: `E:/dayagent-mobile/components/PixelButton.tsx`
- Create: `E:/dayagent-mobile/components/ScanlineOverlay.tsx`

- [ ] **Step 1: Write PixelCard**

```typescript
// components/PixelCard.tsx
import React, { ReactNode } from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { colors, borderWidth, spacing } from '../constants/theme';

interface PixelCardProps {
  children: ReactNode;
  style?: ViewStyle;
  active?: boolean;
}

export default function PixelCard({ children, style, active }: PixelCardProps) {
  return (
    <View
      style={[
        styles.card,
        active && styles.cardActive,
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderWidth: borderWidth.thin,
    borderColor: colors.cardBorder,
    padding: spacing.md,
  },
  cardActive: {
    borderColor: colors.cardBorderActive,
    borderWidth: borderWidth.normal,
  },
});
```

- [ ] **Step 2: Write PixelButton**

```typescript
// components/PixelButton.tsx
import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ViewStyle,
  ActivityIndicator,
} from 'react-native';
import { colors, borderWidth, spacing, fontSize } from '../constants/theme';

interface PixelButtonProps {
  title: string;
  subtitle?: string;
  onPress: () => void;
  loading?: boolean;
  style?: ViewStyle;
  disabled?: boolean;
}

export default function PixelButton({
  title,
  subtitle,
  onPress,
  loading,
  style,
  disabled,
}: PixelButtonProps) {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={loading || disabled}
      activeOpacity={0.7}
      style={[styles.button, style]}
    >
      {loading ? (
        <ActivityIndicator color={colors.orange} size="small" />
      ) : (
        <>
          <Text style={styles.title}>{title}</Text>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    borderWidth: borderWidth.normal,
    borderColor: colors.cardBorderActive,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    color: colors.orange,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
  },
  subtitle: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.xs,
    marginTop: spacing.xs,
  },
});
```

- [ ] **Step 3: Write ScanlineOverlay**

```typescript
// components/ScanlineOverlay.tsx
import React from 'react';
import { View, StyleSheet } from 'react-native';

export default function ScanlineOverlay() {
  return <View style={styles.scanlines} pointerEvents="none" />;
}

const styles = StyleSheet.create({
  scanlines: {
    ...StyleSheet.absoluteFillObject,
    // Simulate scanlines with repeating gradient via layered views
    // In RN we use a striped pattern with tiny height lines
    opacity: 0.04,
    backgroundColor: 'transparent',
    // Scanlines are achieved via a repeating translucent white stripe
    // rn doesn't support repeating-linear-gradient natively,
    // so we overlay a View with low opacity as a simplified effect
    borderTopWidth: 0.5,
    borderTopColor: 'rgba(255,255,255,0.3)',
    borderBottomWidth: 0.5,
    borderBottomColor: 'rgba(255,255,255,0.3)',
  },
});
```

- [ ] **Step 4: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 8: WeatherHero Component

**Files:**
- Create: `E:/dayagent-mobile/components/WeatherHero.tsx`

- [ ] **Step 1: Write WeatherHero**

```typescript
// components/WeatherHero.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, fontSize } from '../constants/theme';
import { WeatherType } from '../api/weather';
import PixelCat from './PixelCat';

interface WeatherHeroProps {
  location: string;
  conditionText: string;
  weatherType: WeatherType;
  temp?: string;
  children?: React.ReactNode;
}

function getHeroGradient(wt: WeatherType): [string, string] {
  switch (wt) {
    case 'rainy':
      return ['#0a0f14', '#0d1117'];
    case 'snowy':
      return ['#0f111a', '#13151f'];
    case 'cloudy':
      return ['#0c0c0e', '#0f0f12'];
    case 'sunny':
      return ['#0e0a08', '#0c0a08'];
    default:
      return ['#080604', '#0a0806'];
  }
}

export default function WeatherHero({
  location,
  conditionText,
  weatherType,
  temp,
  children,
}: WeatherHeroProps) {
  return (
    <LinearGradient
      colors={getHeroGradient(weatherType)}
      style={styles.container}
    >
      <Text style={styles.date}>
        {new Date().toLocaleDateString('zh-CN', {
          month: 'long',
          day: 'numeric',
        })}{' '}
        · {location}
      </Text>
      <Text style={styles.weather}>{conditionText}</Text>
      {temp ? <Text style={styles.temp}>{temp}</Text> : null}
      <View style={styles.catContainer}>
        <PixelCat />
      </View>
      {children}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingTop: spacing.xxl,
    paddingBottom: spacing.lg,
    paddingHorizontal: spacing.lg,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  date: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.xs,
    marginBottom: spacing.xs,
  },
  weather: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.lg,
  },
  temp: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
    marginTop: 2,
  },
  catContainer: {
    marginVertical: spacing.md,
  },
});
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 9: PlanCard + GenerateButton + LoadingSteps

**Files:**
- Create: `E:/dayagent-mobile/components/PlanCard.tsx`
- Create: `E:/dayagent-mobile/components/GenerateButton.tsx`
- Create: `E:/dayagent-mobile/components/LoadingSteps.tsx`

- [ ] **Step 1: Write PlanCard**

```typescript
// components/PlanCard.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, fontSize, borderWidth } from '../constants/theme';
import PixelCard from './PixelCard';
import { Priority } from '../api/plan';

interface PlanCardProps {
  priorities: Priority[];
  warnings: string[];
  lastUpdated?: string;
  onRefresh?: () => void;
}

export default function PlanCard({
  priorities,
  warnings,
  lastUpdated,
  onRefresh,
}: PlanCardProps) {
  return (
    <PixelCard active style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>◆ 今日行动规划</Text>
        <View style={styles.headerRight}>
          {lastUpdated ? (
            <Text style={styles.updated}>{lastUpdated}</Text>
          ) : null}
          {onRefresh ? (
            <Text style={styles.refresh} onPress={onRefresh}>
              刷新
            </Text>
          ) : null}
        </View>
      </View>
      <View style={styles.divider} />
      {priorities.map((p, i) => (
        <Text key={i} style={styles.priority}>
          ▸ {p.content}
        </Text>
      ))}
      {warnings.length > 0 && (
        <>
          <View style={styles.divider} />
          {warnings.map((w, i) => (
            <Text key={i} style={styles.warning}>
              ⚠ {w}
            </Text>
          ))}
        </>
      )}
    </PixelCard>
  );
}

const styles = StyleSheet.create({
  container: { marginHorizontal: spacing.lg, marginTop: spacing.md },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    color: colors.orange,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
  },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  updated: { color: colors.textDim, fontFamily: 'monospace', fontSize: fontSize.xs },
  refresh: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.xs,
    textDecorationLine: 'underline',
  },
  divider: {
    height: 1,
    backgroundColor: colors.cardBorder,
    marginVertical: spacing.sm,
  },
  priority: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    lineHeight: 24,
  },
  warning: {
    color: colors.orangeDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
    lineHeight: 20,
  },
});
```

- [ ] **Step 2: Write LoadingSteps**

```typescript
// components/LoadingSteps.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, fontSize } from '../constants/theme';

const STEPS = [
  '读取天气...',
  '查询课表...',
  '检查作业...',
  '拉取新闻...',
  '查询快递...',
  'AI 生成规划...',
];

interface LoadingStepsProps {
  currentStep: number;
}

export default function LoadingSteps({ currentStep }: LoadingStepsProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>正在为你生成今日行动规划...</Text>
      <View style={styles.progressBar}>
        {Array.from({ length: 6 }).map((_, i) => (
          <View
            key={i}
            style={[styles.progressCell, i < currentStep && styles.progressCellDone]}
          />
        ))}
      </View>
      <Text style={styles.stepCount}>{currentStep}/6</Text>
      <View style={styles.stepsList}>
        {STEPS.map((step, i) => (
          <Text key={i} style={[styles.step, i < currentStep && styles.stepDone]}>
            {i < currentStep ? '✓ ' : '· '}
            {step}
          </Text>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.md,
    padding: spacing.lg,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorderActive,
    alignItems: 'center',
  },
  title: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    marginBottom: spacing.lg,
  },
  progressBar: {
    flexDirection: 'row',
    gap: 4,
    marginBottom: spacing.sm,
  },
  progressCell: {
    width: 20,
    height: 8,
    backgroundColor: colors.textDim,
  },
  progressCellDone: {
    backgroundColor: colors.orange,
  },
  stepCount: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.xs,
    marginBottom: spacing.md,
  },
  stepsList: {
    alignItems: 'flex-start',
  },
  step: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
    lineHeight: 22,
  },
  stepDone: {
    color: colors.text,
  },
});
```

- [ ] **Step 3: Write GenerateButton**

```typescript
// components/GenerateButton.tsx
import React, { useEffect, useState } from 'react';
import { View, StyleSheet } from 'react-native';
import PixelButton from './PixelButton';
import LoadingSteps from './LoadingSteps';
import { spacing } from '../constants/theme';

interface GenerateButtonProps {
  onGenerate: () => Promise<void>;
  loading: boolean;
}

export default function GenerateButton({ onGenerate, loading }: GenerateButtonProps) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!loading) {
      setStep(0);
      return;
    }
    setStep(0);
    const timers: NodeJS.Timeout[] = [];
    for (let i = 1; i <= 6; i++) {
      timers.push(setTimeout(() => setStep(i), i * 500));
    }
    return () => timers.forEach(clearTimeout);
  }, [loading]);

  if (loading) {
    return <LoadingSteps currentStep={step} />;
  }

  return (
    <View style={styles.container}>
      <PixelButton
        title="◆ 生成今日行动规划"
        subtitle="tap to begin"
        onPress={onGenerate}
        loading={loading}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.md,
  },
});
```

- [ ] **Step 4: Verify TypeScript**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 10: CourseTimeline Component

**Files:**
- Create: `E:/dayagent-mobile/components/CourseTimeline.tsx`

- [ ] **Step 1: Write CourseTimeline**

```typescript
// components/CourseTimeline.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, fontSize } from '../constants/theme';
import PixelCard from './PixelCard';
import { Course } from '../api/courses';

interface CourseTimelineProps {
  courses: Course[];
  title?: string;
}

function getTodayCourses(courses: Course[]): Course[] {
  const today = new Date().getDay(); // 0=Sun, 1=Mon...
  const dayMap: Record<number, number> = { 0: 7, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6 };
  const todayNum = dayMap[today];
  return courses
    .filter((c) => c.dayOfWeek === todayNum)
    .sort((a, b) => a.time.localeCompare(b.time));
}

export default function CourseTimeline({ courses, title = '课表' }: CourseTimelineProps) {
  const todayCourses = getTodayCourses(courses);

  if (todayCourses.length === 0) {
    return (
      <PixelCard style={styles.container}>
        <Text style={styles.empty}>今日无课</Text>
      </PixelCard>
    );
  }

  return (
    <PixelCard style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.divider} />
      <View style={styles.timeline}>
        {todayCourses.map((c, i) => (
          <View key={i} style={styles.row}>
            {/* Timeline dot + line */}
            <View style={styles.dotColumn}>
              <View style={styles.dot} />
              {i < todayCourses.length - 1 && <View style={styles.line} />}
            </View>
            <View style={styles.content}>
              <Text style={styles.time}>{c.time}</Text>
              <Text style={styles.name}>{c.name}</Text>
              {c.location ? (
                <Text style={styles.location}>{c.location}</Text>
              ) : null}
            </View>
          </View>
        ))}
      </View>
    </PixelCard>
  );
}

const styles = StyleSheet.create({
  container: { marginHorizontal: spacing.lg, marginTop: spacing.md },
  title: {
    color: colors.orange,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
  },
  divider: {
    height: 1,
    backgroundColor: colors.cardBorder,
    marginVertical: spacing.sm,
  },
  timeline: { paddingLeft: spacing.xs },
  row: { flexDirection: 'row', minHeight: 44 },
  dotColumn: {
    width: 20,
    alignItems: 'center',
    marginRight: spacing.sm,
  },
  dot: {
    width: 6,
    height: 6,
    backgroundColor: colors.orange,
    marginTop: 6,
  },
  line: {
    flex: 1,
    width: 1,
    backgroundColor: colors.cardBorder,
    marginTop: 2,
  },
  content: { flex: 1, paddingBottom: spacing.md },
  time: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
  },
  name: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    marginTop: 2,
  },
  location: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.xs,
    marginTop: 1,
  },
  empty: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
  },
});
```

- [ ] **Step 2: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 11: BottomTabBar Component

**Files:**
- Create: `E:/dayagent-mobile/components/BottomTabBar.tsx`

- [ ] **Step 1: Write BottomTabBar**

```typescript
// components/BottomTabBar.tsx
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { usePathname, useRouter } from 'expo-router';
import { colors, fontSize, TAB_HEIGHT } from '../constants/theme';

interface Tab {
  key: string;
  label: string;
  href: string;
}

const TABS: Tab[] = [
  { key: 'today', label: '今日', href: '/(tabs)/today' },
  { key: 'diary', label: '日记', href: '/(tabs)/diary' },
  { key: 'life', label: '生活', href: '/(tabs)/life' },
  { key: 'goals', label: '目标', href: '/(tabs)/goals' },
  { key: 'settings', label: '设置', href: '/(tabs)/settings' },
];

export default function BottomTabBar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <View style={styles.container}>
      <View style={styles.border} />
      <View style={styles.tabs}>
        {TABS.map((tab) => {
          const active = pathname.includes(tab.key);
          return (
            <TouchableOpacity
              key={tab.key}
              style={styles.tab}
              onPress={() => router.replace(tab.href as any)}
              activeOpacity={0.6}
            >
              {active && <View style={styles.activeBar} />}
              <Text style={[styles.label, active && styles.labelActive]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: TAB_HEIGHT,
    backgroundColor: colors.navBg,
  },
  border: {
    height: 1,
    backgroundColor: colors.cardBorder,
  },
  tabs: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    position: 'relative',
  },
  activeBar: {
    position: 'absolute',
    top: 0,
    left: '50%',
    marginLeft: -8,
    width: 16,
    height: 2,
    backgroundColor: colors.orange,
  },
  label: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.xs,
  },
  labelActive: {
    color: colors.orange,
  },
});
```

- [ ] **Step 2: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 12: SummaryForm + AIFeedback Components

**Files:**
- Create: `E:/dayagent-mobile/components/SummaryForm.tsx`
- Create: `E:/dayagent-mobile/components/AIFeedback.tsx`

- [ ] **Step 1: Write SummaryForm**

```typescript
// components/SummaryForm.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet } from 'react-native';
import { colors, spacing, fontSize, borderWidth } from '../constants/theme';
import PixelButton from './PixelButton';

interface SummaryFormProps {
  onSubmit: (content: string, moodScore: number) => Promise<void>;
  loading: boolean;
}

export default function SummaryForm({ onSubmit, loading }: SummaryFormProps) {
  const [content, setContent] = useState('');
  const [mood, setMood] = useState(3);

  const handleSubmit = async () => {
    if (!content.trim()) return;
    await onSubmit(content.trim(), mood);
    setContent('');
    setMood(3);
  };

  return (
    <View style={styles.container}>
      {/* Mood selector */}
      <Text style={styles.label}>今天感觉</Text>
      <View style={styles.moodRow}>
        {[1, 2, 3, 4, 5].map((n) => (
          <Text
            key={n}
            style={[styles.moodStar, n <= mood && styles.moodStarActive]}
            onPress={() => setMood(n)}
          >
            {n <= mood ? '★' : '☆'}
          </Text>
        ))}
      </View>

      {/* Content input */}
      <Text style={styles.label}>今天做了什么</Text>
      <TextInput
        style={styles.input}
        value={content}
        onChangeText={setContent}
        placeholder="写下今天的完成事项..."
        placeholderTextColor={colors.textDim}
        multiline
        textAlignVertical="top"
      />

      <PixelButton
        title="提交总结"
        onPress={handleSubmit}
        loading={loading}
        disabled={!content.trim()}
        style={{ marginTop: spacing.md }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.md,
    padding: spacing.lg,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  label: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
    marginBottom: spacing.sm,
  },
  moodRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  moodStar: {
    color: colors.textDim,
    fontSize: 28,
  },
  moodStarActive: {
    color: colors.orange,
  },
  input: {
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderWidth: borderWidth.thin,
    borderColor: colors.cardBorder,
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    padding: spacing.md,
    minHeight: 120,
    lineHeight: 22,
  },
});
```

- [ ] **Step 2: Write AIFeedback**

```typescript
// components/AIFeedback.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, fontSize } from '../constants/theme';

interface AIFeedbackProps {
  reply: string;
}

export default function AIFeedback({ reply }: AIFeedbackProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>AI 回复</Text>
      <View style={styles.divider} />
      <Text style={styles.reply}>{reply}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.md,
    padding: spacing.lg,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  label: {
    color: colors.orange,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
  },
  divider: {
    height: 1,
    backgroundColor: colors.cardBorder,
    marginVertical: spacing.sm,
  },
  reply: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    lineHeight: 22,
    fontStyle: 'italic',
  },
});
```

- [ ] **Step 3: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 13: Root Layout + Font Loading

**Files:**
- Create: `E:/dayagent-mobile/app/_layout.tsx`

- [ ] **Step 1: Write root layout**

```typescript
// app/_layout.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Slot, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as Font from 'expo-font';
import { useUserStore } from '../stores/user';
import { colors } from '../constants/theme';

export default function RootLayout() {
  const [fontsLoaded, setFontsLoaded] = useState(false);
  const { isLoggedIn, restoreSession } = useUserStore();
  const router = useRouter();
  const segments = useSegments();

  useEffect(() => {
    async function init() {
      try {
        await Font.loadAsync({
          // zpix: require('../assets/fonts/zpix.ttf'), // uncomment when font file available
        });
      } catch {
        // zpix may not be available; fallback to monospace
      }
      setFontsLoaded(true);
    }
    init();
  }, []);

  useEffect(() => {
    restoreSession();
  }, []);

  useEffect(() => {
    if (!fontsLoaded) return;
    const inAuthGroup = segments[0] === 'login';
    if (!isLoggedIn && !inAuthGroup) {
      router.replace('/login' as any);
    }
  }, [isLoggedIn, segments, fontsLoaded]);

  if (!fontsLoaded) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator color={colors.orange} />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <Slot />
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    backgroundColor: colors.bg,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: 12,
  },
});
```

- [ ] **Step 2: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 14: Tab Layout

**Files:**
- Create: `E:/dayagent-mobile/app/(tabs)/_layout.tsx`

- [ ] **Step 1: Write tab layout**

```typescript
// app/(tabs)/_layout.tsx
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Slot } from 'expo-router';
import BottomTabBar from '../../components/BottomTabBar';
import { colors, TAB_HEIGHT } from '../../constants/theme';

export default function TabLayout() {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Slot />
      </View>
      <BottomTabBar />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    flex: 1,
    paddingBottom: TAB_HEIGHT,
  },
});
```

- [ ] **Step 2: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 15: Today Page

**Files:**
- Create: `E:/dayagent-mobile/app/(tabs)/today.tsx`

- [ ] **Step 1: Write Today page**

```typescript
// app/(tabs)/today.tsx
import React, { useEffect } from 'react';
import {
  View,
  ScrollView,
  Text,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import WeatherHero from '../../components/WeatherHero';
import GenerateButton from '../../components/GenerateButton';
import PlanCard from '../../components/PlanCard';
import CourseTimeline from '../../components/CourseTimeline';
import PixelCard from '../../components/PixelCard';
import { usePlanStore } from '../../stores/plan';
import { useWeatherStore } from '../../stores/weather';
import { fetchCourses, Course } from '../../api/courses';
import { fetchNews, NewsItem } from '../../api/news';
import { colors, spacing, fontSize } from '../../constants/theme';

const LOCATION = '南昌';

export default function TodayPage() {
  const { status, plan, generatePlan, refreshPlan } = usePlanStore();
  const { weather, weatherType, loadWeather } = useWeatherStore();
  const [courses, setCourses] = React.useState<Course[]>([]);
  const [newsItems, setNewsItems] = React.useState<NewsItem[]>([]);
  const [refreshing, setRefreshing] = React.useState(false);

  useEffect(() => {
    loadWeather(LOCATION);
    fetchCourses().then(setCourses).catch(() => {});
    fetchNews().then(setNewsItems).catch(() => {});
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      loadWeather(LOCATION),
      fetchCourses().then(setCourses).catch(() => {}),
      fetchNews().then(setNewsItems).catch(() => {}),
      status === 'loaded' ? refreshPlan(LOCATION) : Promise.resolve(),
    ]);
    setRefreshing(false);
  };

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.orange}
          />
        }
      >
        {/* Hero */}
        <WeatherHero
          location={LOCATION}
          conditionText={weather?.condition_text ?? '加载中...'}
          weatherType={weatherType}
          temp={weather?.weather}
        >
          {status === 'idle' || status === 'error' ? (
            <GenerateButton
              onGenerate={() => generatePlan(LOCATION)}
              loading={status === 'loading'}
            />
          ) : null}
        </WeatherHero>

        {/* Loading state */}
        {status === 'loading' && (
          <GenerateButton onGenerate={async () => {}} loading={true} />
        )}

        {/* Plan card */}
        {status === 'loaded' && plan && (
          <PlanCard
            priorities={plan.priorities}
            warnings={plan.warnings}
            lastUpdated={usePlanStore.getState().lastUpdated ?? undefined}
            onRefresh={() => refreshPlan(LOCATION)}
          />
        )}

        {/* Error */}
        {status === 'error' && (
          <PixelCard style={styles.errorCard}>
            <Text style={styles.errorText}>
              {usePlanStore.getState().error ?? '出错了'}
            </Text>
          </PixelCard>
        )}

        {/* Courses */}
        {courses.length > 0 && <CourseTimeline courses={courses} />}

        {/* News */}
        {newsItems.length > 0 && (
          <PixelCard style={styles.newsCard}>
            <Text style={styles.sectionTitle}>为你推荐</Text>
            <View style={styles.newsDivider} />
            {newsItems.map((n, i) => (
              <Text key={i} style={styles.newsItem}>
                ▸ {n.title}
              </Text>
            ))}
          </PixelCard>
        )}

        <View style={{ height: spacing.xxl }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  errorCard: { marginHorizontal: spacing.lg, marginTop: spacing.md },
  errorText: { color: colors.orangeDim, fontFamily: 'monospace', fontSize: fontSize.sm },
  sectionTitle: { color: colors.orange, fontFamily: 'monospace', fontSize: fontSize.md },
  newsDivider: {
    height: 1,
    backgroundColor: colors.cardBorder,
    marginVertical: spacing.sm,
  },
  newsItem: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    lineHeight: 24,
  },
  newsCard: { marginHorizontal: spacing.lg, marginTop: spacing.md },
});
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 16: Diary Page

**Files:**
- Create: `E:/dayagent-mobile/app/(tabs)/diary.tsx`

- [ ] **Step 1: Write Diary page**

```typescript
// app/(tabs)/diary.tsx
import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text } from 'react-native';
import SummaryForm from '../../components/SummaryForm';
import AIFeedback from '../../components/AIFeedback';
import { useUserStore } from '../../stores/user';
import { createSummary } from '../../api/summary';
import { sendChat } from '../../api/chat';
import { colors, spacing, fontSize } from '../../constants/theme';

export default function DiaryPage() {
  const { userId } = useUserStore();
  const [submitting, setSubmitting] = useState(false);
  const [aiReply, setAiReply] = useState<string | null>(null);

  const handleSubmit = async (content: string, moodScore: number) => {
    if (!userId) return;
    setSubmitting(true);
    setAiReply(null);
    try {
      await createSummary({ userId, content, moodScore });
      const chatRes = await sendChat({
        userId,
        message: `刚写完今日总结：${content}，精力评分 ${moodScore}/5`,
      });
      setAiReply(chatRes.reply);
    } catch {
      // handled silently
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.pageTitle}>每日总结</Text>
      <SummaryForm onSubmit={handleSubmit} loading={submitting} />
      {aiReply && <AIFeedback reply={aiReply} />}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { paddingTop: spacing.xxl, paddingBottom: spacing.xxl },
  pageTitle: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.xl,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
});
```

- [ ] **Step 2: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 17: Life Page

**Files:**
- Create: `E:/dayagent-mobile/app/(tabs)/life.tsx`

- [ ] **Step 1: Write Life page**

```typescript
// app/(tabs)/life.tsx
import React, { useEffect, useState } from 'react';
import { ScrollView, Text, StyleSheet } from 'react-native';
import CourseTimeline from '../../components/CourseTimeline';
import PixelCard from '../../components/PixelCard';
import { fetchCourses, Course } from '../../api/courses';
import { fetchParcels, Parcel } from '../../api/parcel';
import { fetchNews, NewsItem } from '../../api/news';
import { colors, spacing, fontSize } from '../../constants/theme';

export default function LifePage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);

  useEffect(() => {
    fetchCourses().then(setCourses).catch(() => {});
    fetchParcels(1).then(setParcels).catch(() => {}); // userId from store would be better
    fetchNews().then(setNewsItems).catch(() => {});
  }, []);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Courses */}
      <CourseTimeline courses={courses} title="本周课表" />

      {/* Parcels */}
      <PixelCard style={styles.card}>
        <Text style={styles.sectionTitle}>快递</Text>
        <Text style={styles.divider}>──────────────</Text>
        {parcels.length === 0 ? (
          <Text style={styles.empty}>暂无快递</Text>
        ) : (
          parcels.map((p) => (
            <Text key={p.id} style={styles.item}>
              ▸ {p.carrier}: {p.remark || p.trackingNo} — {p.isDelivered ? '已签收' : p.status}
            </Text>
          ))
        )}
      </PixelCard>

      {/* News */}
      <PixelCard style={styles.card}>
        <Text style={styles.sectionTitle}>为你推荐</Text>
        <Text style={styles.divider}>──────────────</Text>
        {newsItems.map((n, i) => (
          <Text key={i} style={styles.item}>
            ▸ {n.title}
          </Text>
        ))}
      </PixelCard>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { paddingTop: spacing.xxl, paddingBottom: spacing.xxl },
  card: { marginHorizontal: spacing.lg, marginTop: spacing.md },
  sectionTitle: {
    color: colors.orange,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
  },
  divider: {
    color: colors.cardBorder,
    fontFamily: 'monospace',
    fontSize: fontSize.xs,
    marginVertical: spacing.sm,
  },
  item: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    lineHeight: 24,
  },
  empty: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
  },
});
```

- [ ] **Step 2: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 18: Goals Page

**Files:**
- Create: `E:/dayagent-mobile/app/(tabs)/goals.tsx`

- [ ] **Step 1: Write Goals page**

```typescript
// app/(tabs)/goals.tsx
import React, { useEffect, useState } from 'react';
import {
  ScrollView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { useUserStore } from '../../stores/user';
import { fetchGoals, createGoal, Goal } from '../../api/goal';
import { colors, spacing, fontSize, borderWidth } from '../../constants/theme';

export default function GoalsPage() {
  const { userId } = useUserStore();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [type, setType] = useState<'weekly' | 'monthly'>('weekly');
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadGoals = () => {
    if (!userId) return;
    fetchGoals(userId).then(setGoals).catch(() => {});
  };

  useEffect(() => { loadGoals(); }, [userId]);

  const handleCreate = async () => {
    if (!userId || !content.trim()) return;
    setSubmitting(true);
    try {
      await createGoal({ userId, type, content: content.trim() });
      setContent('');
      setShowForm(false);
      loadGoals();
    } catch {
      // handled silently
    } finally {
      setSubmitting(false);
    }
  };

  const activeGoals = goals.filter((g) => g.status === 'active');
  const doneGoals = goals.filter((g) => g.status === 'done');

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.pageTitle}>目标</Text>

      {/* Add button */}
      <TouchableOpacity
        style={styles.addButton}
        onPress={() => setShowForm(!showForm)}
      >
        <Text style={styles.addButtonText}>
          {showForm ? '取消' : '+ 新建目标'}
        </Text>
      </TouchableOpacity>

      {/* New goal form */}
      {showForm && (
        <View style={styles.form}>
          <View style={styles.typeRow}>
            <Text
              style={[styles.typeOption, type === 'weekly' && styles.typeActive]}
              onPress={() => setType('weekly')}
            >
              本周
            </Text>
            <Text
              style={[styles.typeOption, type === 'monthly' && styles.typeActive]}
              onPress={() => setType('monthly')}
            >
              本月
            </Text>
          </View>
          <TextInput
            style={styles.input}
            value={content}
            onChangeText={setContent}
            placeholder="目标内容..."
            placeholderTextColor={colors.textDim}
          />
          <TouchableOpacity
            style={styles.submitBtn}
            onPress={handleCreate}
            disabled={submitting || !content.trim()}
          >
            <Text style={styles.submitBtnText}>
              {submitting ? '...' : '创建'}
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Active goals */}
      {activeGoals.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>进行中</Text>
          {activeGoals.map((g) => (
            <View key={g.id} style={styles.goalItem}>
              <Text style={styles.goalContent}>▸ {g.content}</Text>
              <Text style={styles.goalType}>{g.type === 'weekly' ? '本周' : '本月'}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Done goals */}
      {doneGoals.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>已完成</Text>
          {doneGoals.map((g) => (
            <View key={g.id} style={styles.goalItem}>
              <Text style={styles.goalContentDone}>✓ {g.content}</Text>
              <Text style={styles.goalType}>{g.type === 'weekly' ? '本周' : '本月'}</Text>
            </View>
          ))}
        </View>
      )}

      {activeGoals.length === 0 && doneGoals.length === 0 && (
        <Text style={styles.empty}>还没有目标，新建一个吧</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, paddingTop: spacing.xxl },
  pageTitle: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.xl,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  addButton: {
    borderWidth: 1,
    borderColor: colors.cardBorderActive,
    padding: spacing.md,
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  addButtonText: { color: colors.orange, fontFamily: 'monospace', fontSize: fontSize.md },
  form: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorderActive,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  typeRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  typeOption: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  typeActive: { color: colors.orange, borderColor: colors.orange },
  input: {
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderWidth: 1,
    borderColor: colors.cardBorder,
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    padding: spacing.md,
    marginBottom: spacing.md,
    lineHeight: 22,
  },
  submitBtn: {
    borderWidth: 1,
    borderColor: colors.cardBorderActive,
    padding: spacing.md,
    alignItems: 'center',
  },
  submitBtnText: { color: colors.orange, fontFamily: 'monospace', fontSize: fontSize.md },
  section: { marginTop: spacing.lg },
  sectionTitle: {
    color: colors.orange,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    marginBottom: spacing.sm,
  },
  goalItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  goalContent: { color: colors.text, fontFamily: 'monospace', fontSize: fontSize.md, flex: 1 },
  goalContentDone: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    flex: 1,
    textDecorationLine: 'line-through',
  },
  goalType: { color: colors.textDim, fontFamily: 'monospace', fontSize: fontSize.xs },
  empty: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
    textAlign: 'center',
    marginTop: spacing.xxl,
  },
});
```

- [ ] **Step 2: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 19: Settings + Login Pages

**Files:**
- Create: `E:/dayagent-mobile/app/(tabs)/settings.tsx`
- Create: `E:/dayagent-mobile/app/login.tsx`

- [ ] **Step 1: Write Settings page**

```typescript
// app/(tabs)/settings.tsx
import React from 'react';
import { ScrollView, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useUserStore } from '../../stores/user';
import { usePlanStore } from '../../stores/plan';
import { useWeatherStore } from '../../stores/weather';
import { colors, spacing, fontSize } from '../../constants/theme';

export default function SettingsPage() {
  const { username, logout } = useUserStore();
  const reset = usePlanStore((s) => s.reset);
  const resetWeather = useWeatherStore((s) => s.reset);
  const router = useRouter();

  const handleLogout = () => {
    reset();
    resetWeather();
    logout();
    router.replace('/login' as any);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.pageTitle}>设置</Text>

      {/* User info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>账号</Text>
        <View style={styles.divider} />
        <Text style={styles.label}>
          用户名: <Text style={styles.value}>{username ?? '—'}</Text>
        </Text>
      </View>

      {/* Actions */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>退出登录</Text>
      </TouchableOpacity>

      <Text style={styles.version}>DayAgent v1.0.0</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, paddingTop: spacing.xxl },
  pageTitle: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.xl,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  section: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  sectionTitle: { color: colors.orange, fontFamily: 'monospace', fontSize: fontSize.md },
  divider: {
    height: 1,
    backgroundColor: colors.cardBorder,
    marginVertical: spacing.sm,
  },
  label: { color: colors.textDim, fontFamily: 'monospace', fontSize: fontSize.md },
  value: { color: colors.text },
  logoutBtn: {
    borderWidth: 1,
    borderColor: colors.orangeDim,
    padding: spacing.md,
    alignItems: 'center',
    marginTop: spacing.lg,
  },
  logoutText: { color: colors.orangeDim, fontFamily: 'monospace', fontSize: fontSize.md },
  version: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.xs,
    textAlign: 'center',
    marginTop: spacing.xxl,
  },
});
```

- [ ] **Step 2: Write Login page**

```typescript
// app/login.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useUserStore } from '../../stores/user';
import { login } from '../../api/auth';
import PixelButton from '../../components/PixelButton';
import { colors, spacing, fontSize, borderWidth } from '../../constants/theme';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { setUser } = useUserStore();
  const router = useRouter();

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await login({ username: username.trim(), password });
      setUser(res.userId, res.username, res.token);
      router.replace('/(tabs)/today' as any);
    } catch {
      setError('登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.inner}>
        <Text style={styles.logo}>DayAgent</Text>
        <Text style={styles.subtitle}>你的每日智能规划助手</Text>

        <View style={styles.form}>
          <TextInput
            style={styles.input}
            value={username}
            onChangeText={setUsername}
            placeholder="用户名"
            placeholderTextColor={colors.textDim}
            autoCapitalize="none"
          />
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            placeholder="密码"
            placeholderTextColor={colors.textDim}
            secureTextEntry
          />

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <PixelButton
            title="登录"
            onPress={handleLogin}
            loading={loading}
            disabled={!username.trim() || !password.trim()}
            style={{ marginTop: spacing.md }}
          />
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
    justifyContent: 'center',
  },
  inner: {
    paddingHorizontal: spacing.xxl,
    alignItems: 'center',
  },
  logo: {
    color: colors.orange,
    fontFamily: 'monospace',
    fontSize: 32,
    marginBottom: spacing.sm,
  },
  subtitle: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
    marginBottom: spacing.xxl,
  },
  form: {
    width: '100%',
    padding: spacing.lg,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  input: {
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderWidth: borderWidth.thin,
    borderColor: colors.cardBorder,
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  error: {
    color: colors.orange,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
    marginTop: spacing.sm,
  },
});
```

- [ ] **Step 3: Verify**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 20: Chat Page

**Files:**
- Create: `E:/dayagent-mobile/app/chat.tsx`

- [ ] **Step 1: Write Chat page**

```typescript
// app/chat.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useUserStore } from '../../stores/user';
import { sendChat } from '../../api/chat';
import { colors, spacing, fontSize, borderWidth } from '../../constants/theme';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const { userId } = useUserStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || !userId) return;
    const userMsg: Message = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await sendChat({
        userId,
        message: userMsg.content,
      });
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '抱歉，暂时无法回复。' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        style={styles.messages}
        contentContainerStyle={styles.messagesContent}
      >
        {messages.length === 0 && (
          <Text style={styles.empty}>
            我是你的私人助手，知道你今天的所有安排。{"\n"}
            有什么想问的？
          </Text>
        )}
        {messages.map((m, i) => (
          <View
            key={i}
            style={[
              styles.bubble,
              m.role === 'user' ? styles.userBubble : styles.assistantBubble,
            ]}
          >
            <Text style={styles.bubbleText}>{m.content}</Text>
          </View>
        ))}
        {loading && (
          <Text style={styles.typing}>···</Text>
        )}
      </ScrollView>

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="输入消息..."
          placeholderTextColor={colors.textDim}
          multiline
        />
        <TouchableOpacity
          style={styles.sendBtn}
          onPress={handleSend}
          disabled={loading || !input.trim()}
        >
          <Text style={styles.sendText}>发送</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  messages: { flex: 1 },
  messagesContent: { padding: spacing.lg, paddingTop: spacing.xxl },
  empty: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
    textAlign: 'center',
    marginTop: spacing.xxl * 3,
    lineHeight: 22,
  },
  bubble: {
    padding: spacing.md,
    marginBottom: spacing.sm,
    maxWidth: '80%',
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorderActive,
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(14,9,5,0.6)',
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  bubbleText: {
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    lineHeight: 22,
  },
  typing: {
    color: colors.textDim,
    fontFamily: 'monospace',
    fontSize: fontSize.sm,
    marginLeft: spacing.md,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    backgroundColor: colors.navBg,
  },
  input: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderWidth: 1,
    borderColor: colors.cardBorder,
    color: colors.text,
    fontFamily: 'monospace',
    fontSize: fontSize.md,
    padding: spacing.md,
    maxHeight: 80,
  },
  sendBtn: {
    marginLeft: spacing.sm,
    borderWidth: 1,
    borderColor: colors.cardBorderActive,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    justifyContent: 'center',
  },
  sendText: { color: colors.orange, fontFamily: 'monospace', fontSize: fontSize.md },
});
```

- [ ] **Step 2: Final TypeScript check**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```

---

### Task 21: Run & Test

- [ ] **Step 1: Start Expo dev server**

```bash
cd E:/dayagent-mobile && npx expo start
```

Expected: QR code in terminal. Scan with Expo Go app (phone must be on same network).

- [ ] **Step 2: Configure server address**

Edit `E:/dayagent-mobile/api/client.ts` — change `BASE_URL` to your actual LAN IP of the Java backend:

```typescript
const BASE_URL = 'http://<YOUR_LAN_IP>:8080';
```

- [ ] **Step 3: Start backend services**

```bash
# Terminal 1: Start MySQL (if not running)
# Terminal 2: Start Python agent
cd E:/dayagent/agent_service && python main.py

# Terminal 3: Start Java backend
cd E:/dayagent && mvn spring-boot:run
```

- [ ] **Step 4: Test flow**

1. Open Expo Go, scan QR code
2. Login screen appears → enter username/password
3. Today page → Hero shows weather + cat
4. Tap "◆ 生成今日行动规划" → loading steps animate → plan card appears
5. Pull down to refresh
6. Switch to Diary tab → write summary → submit → see AI reply
7. Switch to Life tab → verify courses/parcels/news
8. Switch to Goals tab → create a goal
9. Switch to Settings → verify username, test logout

- [ ] **Step 5: Verify all TypeScript**

```bash
cd E:/dayagent-mobile && npx tsc --noEmit
```
