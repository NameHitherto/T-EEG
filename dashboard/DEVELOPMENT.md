# T-EEG Dashboard 二次开发指南

> 本项目本质是 **Studio Admin** 模板（Next.js 16 + Tailwind v4 + shadcn/ui）。
> `src/app/(main)/dashboard/*` 下的所有页面都是 **Demo**，数据全来自同目录的 `data.ts` / `data.json` 静态 mock。
> 本指南告诉你：哪些是脚手架、如何新建业务页面、如何接入后端 API、有哪些轮子可复用。

---

## 0. 先认清：什么是脚手架，什么是你的业务

- **复用**：`src/components/ui/*`（shadcn 原子组件）、`src/lib/`（偏好系统、utils）、`dashboard/layout.tsx`（应用外壳：侧边栏 + 顶栏）、`src/stores/preferences`（主题/布局状态）。
- **替换**：`dashboard/*` 下的页面内容、`src/navigation/sidebar/sidebar-items.ts`（导航）、`src/data/users.ts`（占位用户）、`src/config/app-config.ts`（应用名/标题）。
- **新增**：你的业务页面、API 接入层、数据类型。

> 删 Demo 时注意：`/dashboard` 重定向到 `/dashboard/default`（`next.config.mjs`）。要么保留 `default`，要么改这个 redirect。

---

## 1. 前端界面开发

### 1.1 新建一个业务页面（colocation 模式）

这个项目严格遵循 **colocation**：页面、组件、数据、类型全部放在路由同目录下，`_components/` 用 Next 约定的下划线前缀（不可路由）。

新增 `eeg-signals` 页面，结构如下：

```
src/app/(main)/dashboard/eeg-signals/
├── page.tsx              # 路由入口（可 server / 可 client）
├── _components/
│   ├── signal-chart.tsx  # 复用的是单个业务组件
│   └── data.ts           # 类型 + (过渡期)mock
```

最小 `page.tsx`（纯展示，适合走 server component 拉数据）：

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignalChart } from "./_components/signal-chart";
import { getSignals } from "@/lib/api/signals"; // 你自己的接入层（见第 2 节）

export default async function Page() {
  const signals = await getSignals();
  return (
    <div className="@container/main flex flex-col gap-4 md:gap-6">
      <Card>
        <CardHeader><CardTitle>EEG Signals</CardTitle></CardHeader>
        <CardContent><SignalChart data={signals} /></CardContent>
      </Card>
    </div>
  );
}
```

要点：

- 顶层容器用 `@container/main flex flex-col gap-4 md:gap-6`，与模板风格一致（响应式 container query）。
- 需要全出血（无边距）的页面，在内容容器上加 `data-content-padding="false"`，`dashboard/layout.tsx` 会去掉默认 `p-4/p-6`。
- 用 `"use client"` 仅在需要交互/hook 时加；优先 server component 拉数据。

### 1.2 接入侧边栏导航

导航是**声明式**的，改一处即可：

`src/navigation/sidebar/sidebar-items.ts` → `sidebarItems: NavGroup[]`。每个 item 支持 `icon`(lucide)、`comingSoon`、`newTab`、`isNew`、`subItems`（折叠子项）。要加 EEG 入口：

```ts
{ id: 5, label: "EEG", items: [
  { title: "Signals", url: "/dashboard/eeg-signals", icon: Waves },
  { title: "Experiments", url: "/dashboard/eeg-experiments", icon: FlaskConical },
]}
```

侧边栏壳 `app-sidebar.tsx` 会自动渲染 `sidebarItems`，无需改它。删除 Demo 时把对应 group/item 删掉即可。

### 1.3 顶栏定制

`dashboard/layout.tsx` 的 `<header>` 固定了：SidebarTrigger / 搜索 / LayoutControls / ThemeSwitcher / GitHub / AccountSwitcher。改这一处就能调整全局顶栏。`SearchDialog` / `AccountSwitcher` 都是 `_components/sidebar/` 下独立组件，可替换或删除。

### 1.4 样式约定（避免和 Biome 打架）

- Tailwind class 顺序**不要手动排**——Biome `useSortedClasses` 会自动排序，提交前 `npm run check:fix`。
- 主题/布局相关的条件样式用**属性选择器前缀**写，例如 `[html[data-navbar-style=sticky]_&]:sticky`、`[html[data-content-layout=centered]_&]:max-w-screen-2xl`，和模板保持一致。
- 颜色用语义 token（`bg-background`、`text-muted-foreground`、`bg-primary`），不要硬编码十六进制——这样切换主题/暗色模式才生效。

---

## 2. 后端 API 接入（核心）

项目目前**没有任何 API 层**（无 fetch wrapper、无 axios、无 env 文件）。你需要从零搭。有三种方案，按推荐度排序。

### 方案 A（推荐）：`next.config.mjs` rewrites 反向代理 + fetch 封装层

**用途**：开发期规避 CORS、统一前缀、对前端隐藏真实后端地址。

1. 改 `next.config.mjs`，加 `rewrites()`：

```js
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig = {
  // ...existing config...
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND_URL}/:path*` },
    ];
  },
};
```

> 注意：rewrites 的 `source` 不要和 Next 自己的 `/dashboard` 冲突；用 `/api/*` 作前缀最安全。

2. 建环境变量文件 `.env.local`（`.gitignore` 已忽略 `.env*.local`，不会提交）：

```bash
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=/api   # 前端可见的统一前缀
```

3. 建接入层 `src/lib/api/client.ts`（集中配置，单点修改）：

```ts
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

export class ApiError extends Error {
  constructor(public status: number, message: string, public path: string) {
    super(message);
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) throw new ApiError(res.status, `API ${res.status}: ${path}`, path);
  const text = await res.text();
  return (text ? JSON.parse(text) : null) as T;
}
```

4. 业务模块 `src/lib/api/signals.ts`：

```ts
import { apiFetch } from "./client";
import type { Signal } from "@/types/signal";

export const getSignals = () => apiFetch<Signal[]>("/signals");
```

5. 类型放 `src/types/`（顶层约定，新建即可）。

**关键**：rewrites 对**前端浏览器请求**和**同进程的 server component 请求**都生效——所以 `page.tsx` 里 `await getSignals()` 在 server component 中走的也是 `/api/*` → 后端，无需区分环境。

### 方案 B：Route Handler / Server Action 作 BFF

**用途**：需要保密（token 不能下发浏览器）、需要聚合多个后端、需要后端鉴权头注入时。

- Route Handler：`src/app/api/<resource>/route.ts`，内部用服务端 `fetch` 直接打 `process.env.BACKEND_URL`（绕过 rewrites，直连）。
- Server Action：`"use server"` 文件里 export async 函数，复用模板已有的 `src/server/server-actions.ts` 模式（现在它只做 cookie，照抄即可加后端调用）。

```ts
// src/server/signals-actions.ts
"use server";
export async function fetchSignalsServer() {
  const res = await fetch(`${process.env.BACKEND_URL}/signals`, { cache: "no-store" });
  return res.json();
}
```

适合放在需要 mutate（POST/DELETE）或带鉴权的表单提交里。

### 方案 C：前端直连后端（`NEXT_PUBLIC_*`）

**用途**：后端已开 CORS、且不介意暴露真实地址。最少配置：直接在 client component 里 `fetch(process.env.NEXT_PUBLIC_BACKEND_URL + path)`。不推荐用于生产（暴露地址 + CORS 治理麻烦）。

### 关于 `src/proxy.disabled.ts`

项目里这个文件是 Next.js 16 的 **proxy（原 middleware）**，**重命名为 `proxy.ts` 才启用**。它跑在请求边缘，用途是**鉴权重定向/请求改写**（注释里有"已登录就跳 dashboard"的例子），**不适合**用来做 API 转发到另一域名——那是 `rewrites()` 的活。如果你要加登录态守卫（未登录跳 `/auth`），就启用它：

```ts
export function proxy(req: NextRequest) {
  const token = req.cookies.get("session_token")?.value;
  if (!token && req.nextUrl.pathname.startsWith("/dashboard")) {
    return NextResponse.redirect(new URL("/auth/v2/login", req.url));
  }
  return NextResponse.next();
}
```

### 信号数组 / 大数据传输

按 repo 根 `spec.md` 第 6 节：**大型 EEG 信号数组不要塞进单个 JSON**。前端展示长信号时走分页接口 / chunked / 流式 / WebSocket，不要一次性 `res.json()` 拉几十万采样点。图表层做下采样展示。

---

## 3. 复用入口（这些轮子已经有了）

| 场景 | 用什么 | 参考示例 |
|---|---|---|
| 图表 | `recharts`（已装） | `dashboard/default/_components/performance-overview.tsx` |
| 数据表格（筛选/分页/排序/选择） | `@tanstack/react-table` | `dashboard/users/_components/users.tsx` + `users-columns.tsx` |
| 表单 + 校验 | `react-hook-form` + `@hookform/resolvers` + `zod` | `dashboard/auth/*/page.tsx` |
| 弹窗/抽屉/下拉 | shadcn (`@/components/ui/*`：dialog/sheet/drawer/select) | 全项目通用 |
| 通知 | `sonner`（`<Toaster/>` 已在 root layout） | 调 `toast.success(...)` |
| 图标 | `lucide-react` | 侧边栏、各组件 |
| 品牌图标 | `simple-icons` | `src/components/simple-icon.tsx` |
| 地图（logistics demo） | `d3-geo` + `topojson-client` | `logistics/_components/shipment-route-map.tsx` |
| 拖拽（kanban） | `@dnd-kit/*` | `dashboard/kanban/` |

> TanStack Table 那块模板用了 `"use no memo"` 指令（配合 React Compiler），照抄 users 那套写法即可，别去手改。

---

## 4. 推荐的二次开发步骤

1. **清场**：删掉 `dashboard/*` 下用不到的 Demo 页面 + 对应 `sidebar-items.ts` 条目 + 顶层 `/dashboard` redirect（或改指向你的首页）。
2. **接 API**：按方案 A 配 `rewrites` + `.env.local`，建 `src/lib/api/client.ts`、`src/types/`、`src/lib/api/<module>.ts`。
3. **建首页**：在 `dashboard/default/`（或新建目录）写你的第一个真实数据页面，server component + `await getXxx()`。
4. **加导航**：改 `sidebar-items.ts`，加 `src/config/app-config.ts` 里的应用名。
5. **统一数据流**：列表页用 TanStack Table（仿 users），表单页用 RHF + Zod（仿 auth），图表用 recharts。
6. **提交前**：`npm run check:fix`（格式+lint+import 排序）。Husky 会自动跑 `generate:presets` + lint-staged——除非你改了 `src/styles/presets/*.css`，否则不用管 `theme.ts`。

---

## 5. 约定与坑（容易踩的）

- **import 顺序**由 Biome 自动管（react → next → 包 → `@/` → 相对），别手动排。
- **`src/components/ui/**` 免检**：shadcn 原子组件不受 Biome 约束，可自由改；你自己的业务组件放 `src/components/` 顶层（如 `simple-icon.tsx`）会受检。
- **`src/lib/preferences/theme.ts` 是生成的**：`generated:themePresets` 标记区间别手改——改 `src/styles/presets/*.css` 后跑 `npm run generate:presets`。新主题无关业务开发可忽略。
- **Server/Client 边界**：`"use client"` 组件不能直接 `await` async；数据要么在 server page 拉好传 props，要么在 client 组件里用 `useEffect`/SWR。推荐 server page 拉数据传给 client 子组件（如 `<UsersTable>`）。
- **layout-critical 偏好**（`sidebar_variant`/`sidebar_collapsible`）必须能 SSR，所以禁用 `localStorage` 持久化——这是偏好系统的硬约束，新加偏好时注意（详见 `preferences-config.ts`）。
- **Windows 行尾**：Biome 强制 `lf`，确保你的编辑器/git 不会引入 `crlf`（`core.autocrlf input`）。
