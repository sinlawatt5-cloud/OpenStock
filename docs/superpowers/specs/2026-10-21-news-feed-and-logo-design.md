# OpenStock — ข่าวหุ้นย้อนหลัง 24 ชั่วโมงและระบบโลโก้บริษัท

วันที่ออกแบบ: 21 ตุลาคม 2026  
สถานะ: Design approved by user  
ขอบเขต: หน้า News แบบ Timeline Feed, on-demand ingestion, แปล/สรุปไทยรายข่าว, โลโก้จริงทั่วทั้งเว็บ

## 1. เป้าหมาย

เพิ่มหน้า `/news` สำหรับข่าวหุ้นสหรัฐย้อนหลัง 24 ชั่วโมง โดย:

- ครอบคลุมหุ้นใน Watchlist, Movers และหุ้นยอดนิยมประมาณ 30 ตัวจากฐานเดิม
- รวมข่าวจาก yfinance, Yahoo Finance RSS และ RSS/Atom ฟรีที่ตรวจสอบแล้ว
- แปลพาดหัวและสรุปใจความเป็นภาษาไทยด้วย `gemini-3.5-flash-lite`
- ใช้ OpenRouter เป็น fallback และแสดงต้นฉบับอังกฤษเมื่อ AI ทั้งสองเส้นทางล้มเหลว
- แสดงแหล่งข่าว เวลา ticker และลิงก์ต้นฉบับทุกข่าว
- แสดงโลโก้บริษัทจริงอย่างสม่ำเสมอทั่วทั้งเว็บ พร้อม initials fallback
- อัปเดตข่าวเฉพาะเมื่อผู้ใช้กด Refresh ไม่มี scheduler ในเวอร์ชันแรก

## 2. การตัดสินใจที่ยืนยันแล้ว

| ประเด็น | การตัดสินใจ |
|---|---|
| ขอบเขตหุ้น | Watchlist + Gainers/Losers/Most Active + หุ้นยอดนิยมประมาณ 30 ตัว |
| AI หลัก | Gemini `gemini-3.5-flash-lite` |
| AI fallback | OpenRouter |
| ภาษาต้นทาง | สำนักข่าวต่างประเทศภาษาอังกฤษ |
| ข้อมูลที่ส่งให้ AI | พาดหัว + RSS/Yahoo description/snippet เท่านั้น |
| การอัปเดต | ผู้ใช้กด Refresh เอง |
| Architecture | On-demand ingestion + persistent SQLite cache |
| Layout | Summary + Timeline Feed |
| โลโก้ | Resolve จากแหล่งจริงและ cache ในระบบ |

## 3. แหล่งข้อมูล

### 3.1 แหล่งหลักรายหุ้น

1. `yfinance.Ticker(symbol).news`
2. Yahoo Finance RSS ราย ticker: `https://finance.yahoo.com/rss/headline?s={SYMBOL}`
3. SEC EDGAR Atom สำหรับเอกสารสำคัญ เช่น 8-K

### 3.2 แหล่งข่าวตลาด

1. CNBC Markets RSS: `https://www.cnbc.com/id/100003114/device/rss/rss.html`
2. MarketWatch Top Stories RSS: `https://feeds.marketwatch.com/marketwatch/topstories/`

### 3.3 Fallback

Google News RSS Search ราย ticker ใช้เฉพาะเมื่อแหล่งหลักมีข่าวไม่เพียงพอ โดยแสดง publisher ต้นทาง ไม่แสดง Google News เป็นเจ้าของข่าว

### 3.4 หลักฐานความพร้อมใช้งาน

ทดสอบ endpoint วันที่ 21 ตุลาคม 2026:

- Yahoo Finance RSS: HTTP 200, `application/xml`
- CNBC RSS: HTTP 200, `application/xml`
- MarketWatch RSS: HTTP 200, `application/xml`
- Google News RSS: HTTP 200, `application/xml`
- SEC EDGAR Atom: HTTP 200, `application/atom+xml`
- Nasdaq RSS: timeout จึงไม่ใช้เป็นแหล่งหลัก
- Reuters: ไม่มี RSS ฟรีที่เสถียรสำหรับขอบเขตนี้ จึงไม่รวม

### 3.5 ข้อจำกัดแหล่งข้อมูล

- ไม่ scrape เนื้อหาบทความเต็ม
- ไม่ข้าม paywall
- RSS URLs เป็น allowlist ใน backend ผู้ใช้ไม่สามารถส่ง URL เอง
- SEC requests ต้องมี User-Agent ระบุชื่อแอปและช่องทางติดต่อ
- provider บางตัวล้มเหลวได้โดยไม่ทำให้ feed ทั้งหมดล้มเหลว

## 4. UX หน้า `/news`

### 4.1 Desktop

- หัวหน้า: ชื่อหน้า, จำนวนข่าว, เวลาอัปเดตล่าสุด และปุ่ม `รีเฟรชข่าว`
- คอลัมน์ซ้าย: สรุปภาพรวม 24 ชั่วโมงและตัวกรอง
- คอลัมน์ขวา: Timeline Feed เรียงข่าวใหม่ไปเก่า

### 4.2 Mobile

- สรุปภาพรวมอยู่ด้านบน
- ตัวกรองเป็น horizontal chips
- Timeline Feed เป็นคอลัมน์เดียว
- viewport 390px ต้องไม่มี horizontal overflow

### 4.3 ข่าวแต่ละรายการ

- โลโก้บริษัทจริงหรือ initials fallback
- ชื่อบริษัทและ ticker
- พาดหัวภาษาไทย
- สรุปไทย 1–2 ประโยค ประมาณไม่เกิน 60 คำ
- สำนักข่าวและเวลาย้อนหลัง
- badge `Gemini`, `OpenRouter` หรือ `รอแปล`
- ปุ่ม `อ่านต้นฉบับ` เปิดแท็บใหม่ด้วย `noopener noreferrer`
- ข่าวที่เกี่ยวข้องหลายหุ้นแสดงสูงสุด 3 ticker และ `+N`

### 4.4 ตัวกรองและ URL state

รองรับ:

- ทั้งหมด
- Watchlist
- Movers
- หุ้นยอดนิยม
- ticker รายตัว
- แหล่งข่าว
- สถานะคำแปล

เก็บ state ใน query string เช่น:

```text
/news?scope=watchlist&symbol=NVDA&source=Yahoo
```

### 4.5 Refresh interaction

1. ผู้ใช้กด `รีเฟรชข่าว`
2. Backend สร้าง refresh run และตอบกลับทันที
3. UI แสดง stage: กำลังดึงข่าว → กำลังแปลข่าวใหม่ → เสร็จแล้ว
4. ข่าวเดิมยังอ่านได้ระหว่าง refresh
5. ป้องกันการกดซ้ำขณะมี refresh run ทำงาน
6. Frontend poll สถานะทุกประมาณ 1.5–2 วินาทีเฉพาะระหว่าง run
7. เมื่อ run จบ invalidate feed query และหยุด polling
8. ไม่มี automatic refresh

## 5. Architecture และ Data Flow

```text
Yahoo/yfinance + CNBC/MarketWatch + SEC + Google News fallback
  → fetch และ normalize
  → กรอง published_at ย้อนหลัง 24 ชั่วโมง
  → canonicalize URL และ dedupe
  → persist ข่าวต้นฉบับใน SQLite
  → แปลเฉพาะ content_hash ที่ยังไม่มีผลลัพธ์
  → Gemini 3.5 Flash Lite
  → OpenRouter fallback
  → English fallback
  → resolve/cache โลโก้
  → FastAPI
  → React /news
```

เมื่อเปิดหน้า ระบบอ่าน SQLite ทันที ไม่รอ network ภายนอก เมื่อกด Refresh จึงเริ่ม ingestion แบบ asynchronous ภายใน process

## 6. Database Schema

### 6.1 `news_articles`

| Field | ชนิด/ความหมาย |
|---|---|
| `id` | stable hash; primary key |
| `title_original` | พาดหัวต้นฉบับ |
| `description_original` | RSS/Yahoo snippet ที่ sanitize แล้ว |
| `title_th` | พาดหัวภาษาไทย nullable |
| `summary_th` | สรุปภาษาไทย nullable |
| `canonical_url` | ลิงก์ต้นฉบับ normalized; unique เมื่อมีค่า |
| `source` | ชื่อ publisher |
| `published_at` | UTC datetime |
| `translation_status` | `pending`, `ready`, `fallback`, `failed` |
| `translation_provider` | `gemini`, `openrouter`, `none` |
| `translation_model` | model identifier |
| `content_hash` | hash ของ title + description สำหรับ LLM cache |
| `created_at`, `updated_at` | timestamps |

สถานะคำแปลมีความหมายตายตัว:

- `pending`: รอประมวลผล
- `ready`: Gemini สำเร็จ
- `fallback`: OpenRouter สำเร็จ
- `failed`: ทั้งสองเส้นทางล้มเหลว แสดงอังกฤษด้วย badge `รอแปล` และลองใหม่ใน refresh ถัดไป

Indexes:

- `published_at DESC`
- `(translation_status, published_at DESC)`
- `content_hash`
- `source`

### 6.2 `news_article_symbols`

| Field | ความหมาย |
|---|---|
| `article_id` | FK ไป `news_articles.id` |
| `symbol` | ticker uppercase |
| `confidence` | confidence 0–1 |
| `detection_source` | `provider`, `rss_query`, `title_match` |

Primary key: `(article_id, symbol)`  
Index: `(symbol, article_id)`

### 6.3 `symbol_logos`

| Field | ความหมาย |
|---|---|
| `symbol` | primary key |
| `logo_path` | cached local path nullable |
| `source_url` | URL ที่พบโลโก้ |
| `logo_source` | `yahoo`, `official_site`, `curated` |
| `website` | เว็บไซต์ทางการ |
| `status` | `ready`, `pending`, `failed` |
| `etag`, `content_type` | cache metadata |
| `updated_at` | เวลา resolve ล่าสุด |

### 6.4 `news_refresh_runs`

| Field | ความหมาย |
|---|---|
| `id` | run identifier |
| `status` | `queued`, `fetching`, `translating`, `completed`, `partial`, `failed` |
| `stage` | ข้อความ stage สำหรับ UI |
| `fetched`, `inserted`, `translated` | counters |
| `errors_json` | provider-level errors ที่เปิดเผยได้ |
| `started_at`, `finished_at` | timestamps |

ระบบต้องคืน run ที่กำลังทำงานอยู่แทนการสร้าง run ซ้ำ

## 7. API Design

### 7.1 Timeline Feed

```http
GET /api/news/24h
```

Parameters:

```text
scope=all|watchlist|movers|popular
symbols=NVDA,AAPL
sources=Yahoo Finance,CNBC
translation=all|ready|pending
limit=30
cursor=<published_at,id>
```

ใช้ cursor pagination เพื่อไม่ให้ข่าวกระโดดเมื่อมีรายการใหม่

Response:

```json
{
  "items": [],
  "summary": {},
  "nextCursor": null,
  "asOf": "2026-10-21T16:00:00Z",
  "lastRefresh": "2026-10-21T15:55:00Z",
  "warnings": []
}
```

แต่ละ item รวม ticker metadata และ `logoUrl` ที่พร้อมใช้

### 7.2 เริ่ม Refresh

```http
POST /api/news/refresh
Content-Type: application/json

{
  "watchlistSymbols": ["NVDA", "AAPL"]
}
```

Watchlist อยู่ใน browser local storage จึงต้องส่ง symbols มากับ request; backend จะรวมรายการนี้กับ Movers ใน cache และ Popular 30 ตัวจากฐานข้อมูลแล้ว dedupe

- validate ticker format และจำกัดจำนวน `watchlistSymbols`
- หากมี active run คืน run เดิม
- ตอบ `202 Accepted`

### 7.3 สถานะ Refresh

```http
GET /api/news/refresh/{run_id}
```

คืน status, stage, counters และ errors ที่เหมาะกับ UI

### 7.4 สรุปภาพรวม

```http
GET /api/news/24h/summary
```

สรุปจากข่าว `ready` ล่าสุดและ cache ตามชุด article IDs หากชุดข่าวไม่เปลี่ยนไม่เรียก AI ซ้ำ

### 7.5 โลโก้

```http
GET /api/logos/{symbol}
```

คืน cached image พร้อม `Cache-Control` และ `ETag` หรือ 404 เพื่อให้ frontend ใช้ initials

### 7.6 Backward Compatibility

คง `/api/news` และ `/api/news/summary` เดิมสำหรับ Dashboard ไม่เปลี่ยน response contract

## 8. Normalization และ Dedupe

1. แปลงเวลาเป็น UTC
2. ตัดข่าวเก่ากว่า 24 ชั่วโมง
3. ลบ tracking parameters เช่น `utm_*`
4. บังคับ URL scheme เป็น HTTPS
5. dedupe ด้วย canonical URL
6. dedupe ซ้ำด้วย normalized title hash
7. กรณีข่าวซ้ำเก็บรายการที่ description ครบกว่า เวลาแน่นอนกว่า และมาจาก publisher ต้นทางมากกว่า aggregator
8. หากไม่มี `published_at` ที่เชื่อถือได้ ไม่รวมใน feed 24 ชั่วโมง
9. sanitize HTML จาก description ก่อนบันทึกและก่อนส่ง AI/frontend
10. หน้า `/news` query เฉพาะ 24 ชั่วโมงล่าสุด แต่เก็บข้อมูลไว้ 7 วันสำหรับ dedupe และ audit เบื้องต้น
11. ทุก refresh ที่สำเร็จหรือ partial จะ prune ข่าวและความสัมพันธ์ที่เก่ากว่า 7 วัน พร้อมล้าง translation/logo metadata ที่ไม่ถูกใช้งานตามกติกาแยก

## 9. AI Translation Pipeline

### 9.1 Model Routing

```text
gemini-3.5-flash-lite
  → OpenRouter configured model
  → untranslated English fallback
```

เส้นทางแปลรายข่าวใช้ชื่อ Gemini ที่กำหนดตรงตัว ไม่สลับไป Gemini รุ่นอื่นอย่างเงียบ ๆ

### 9.2 Input

ส่งเฉพาะ:

- stable article ID
- ticker และชื่อบริษัท
- title
- sanitized description/snippet
- source
- published time

ไม่ส่ง HTML เต็มหน้าและไม่ scrape บทความ

### 9.3 Structured Output

```json
{
  "id": "article-id",
  "titleTh": "...",
  "summaryTh": "..."
}
```

### 9.4 Prompt Rules

- แปลตรงความหมาย ไม่ใช้ clickbait
- summary 1–2 ประโยค ประมาณไม่เกิน 60 คำ
- รักษาชื่อบริษัท บุคคล ticker และตัวเลข
- ห้ามแต่งข้อเท็จจริง ราคา เหตุผล หรือผลกระทบ
- ห้ามให้คำแนะนำลงทุน
- ใช้ภาษาไทยธุรกิจที่กระชับและเป็นกลาง
- temperature 0.1–0.2

### 9.5 Quota Control

- batch ครั้งละประมาณ 5–8 ข่าว
- cache ตาม `content_hash`
- แปลเฉพาะข่าวใหม่
- จำกัดจำนวนข่าวต่อ refresh
- retry เฉพาะ `pending/failed` ใน refresh ครั้งถัดไป
- structured output ต้องผ่าน validation ก่อนบันทึก

## 10. Logo System

### 10.1 Resolution Order

```text
Yahoo logoUrl
→ official company website
→ favicon/web manifest ของเว็บไซต์ทางการ
→ curated mapping สำหรับ Popular 30 และ ETF หลัก
→ initials fallback
```

### 10.2 Validation และ Storage

- HTTPS only
- validate MIME type และ file signature
- จำกัด file size และ dimensions
- sanitize/convert เป็น PNG หรือ WebP เมื่อจำเป็น
- เก็บไฟล์ใน local data directory ที่ไม่ commit เข้า Git
- ไม่ hotlink ภายนอกใน UI
- เก็บ `logo_source` เพื่อ audit

### 10.3 Rollout ทั่วเว็บ

เพิ่ม logo metadata และใช้ `Avatar` component กลางใน:

- News Timeline
- Dashboard Movers
- Search Dialog
- Watchlist
- Symbol header
- Peer stocks
- Flows/ETF rows
- ticker chips ที่มีพื้นที่เพียงพอ

ดัชนี สินค้าโภคภัณฑ์ และสินทรัพย์ที่ไม่มีโลโก้บริษัท ใช้ไอคอนประเภทสินทรัพย์แทน

`Avatar` ต้องรองรับ `img.onError` และเปลี่ยนเป็น initials โดยไม่เกิด broken image

## 11. Error Handling

- provider บางตัวล้มเหลว → run เป็น `partial`; feed cache ยังแสดงได้
- providers ทั้งหมดล้มเหลว → run เป็น `failed`; ข้อมูลเดิมไม่ถูกลบ
- Gemini ล้มเหลว → OpenRouter
- AI ทั้งสองล้มเหลว → ต้นฉบับอังกฤษ + badge `รอแปล`
- ข่าวใหม่เป็นศูนย์ → completed พร้อมข้อความว่าไม่มีข่าวใหม่
- โลโก้ resolve ไม่ได้ → initials
- ไม่มีข่าวใน 24 ชั่วโมง → empty state; ไม่เติมข่าวเก่าเข้ามา
- frontend ต้องแยก warning แบบ recoverable ออกจาก fatal error

## 12. Security

- allowlist RSS/Atom endpoints
- XML parser ป้องกัน external entities/entity expansion
- จำกัด response size, timeout และ redirects
- validate HTTPS URLs ก่อนเก็บหรือเปิด
- sanitize RSS HTML
- API keys อยู่ backend `.env` เท่านั้น
- ไม่ส่ง prompt, API key หรือรายละเอียดภายในของ provider ไป frontend
- logo fetcher ป้องกัน SSRF และ private-network destinations
- external links ใช้ `noopener noreferrer`

## 13. Testing Strategy

### 13.1 Backend

- RSS/Atom parsing จาก fixtures ของทุก provider
- 24-hour boundary และ timezone
- canonical URL และ dedupe
- ticker mapping
- Gemini structured output validation
- Gemini fail → OpenRouter
- AI ทั้งสอง fail → English fallback
- LLM cache ป้องกันการแปลซ้ำ
- concurrent refresh deduplication
- partial provider failure
- cursor pagination
- logo validation, cache และ fallback
- unit tests ใช้ mock network ไม่พึ่ง provider จริง

### 13.2 Frontend

- Timeline Feed เรียงใหม่ไปเก่า
- query-string filters
- pending/ready/fallback badges
- refresh progress และป้องกันกดซ้ำ
- cursor `โหลดเพิ่มเติม`
- logo `onError` → initials
- loading, empty, partial warning และ fatal error states
- mobile 390px ไม่มี horizontal overflow

### 13.3 E2E

1. `/news` แสดง cache ทันที
2. Refresh แสดง progress
3. ข่าวเดิมยังอยู่ระหว่าง refresh
4. ข่าวใหม่ปรากฏเมื่อ run เสร็จ
5. filters Watchlist/Movers/Popular ทำงาน
6. เปิดต้นฉบับในแท็บใหม่
7. provider/AI failure แสดง fallback
8. โลโก้ทำงานใน News, Movers, Search, Watchlist และ Symbol

## 14. Definition of Done

- Backend pytest ผ่าน
- Frontend Vitest ผ่าน
- TypeScript build ผ่าน
- lint ไม่มี error ใหม่
- Playwright scenarios ผ่าน
- ไม่มี API key หรือ cached logo binaries ใน Git
- ข่าวทุกชิ้นมี source และลิงก์ตรวจสอบได้
- ผลแปลไม่เติมข้อเท็จจริงใหม่
- โลโก้มี fallback ทุกตำแหน่ง
- เอกสาร API/types อัปเดต
- ไม่ deploy หรือ push implementation จนผู้ใช้อนุญาต

## 15. Non-goals

- ไม่มี scheduler หรือ persistent worker queue
- ไม่ scrape บทความเต็ม
- ไม่ข้าม paywall
- ไม่ติดตามหุ้นสหรัฐทั้งหมด
- ไม่วิเคราะห์ sentiment หรือสร้างคำแนะนำซื้อขาย
- ไม่รับประกัน availability ของ RSS ภายนอก
- ไม่ deploy ในงานออกแบบนี้

## 16. Implementation Boundaries

ขอบเขตงานแบ่งเป็นหน่วยที่ทดสอบแยกได้:

1. Database migrations/repository methods
2. RSS/Yahoo/SEC providers และ normalization
3. Ingestion/dedupe/refresh-run orchestration
4. Gemini/OpenRouter translation pipeline
5. Logo resolver/cache/API
6. News API contracts
7. Timeline Feed UI และ filters
8. Global logo rollout
9. Automated tests และ documentation

แต่ละหน่วยต้องใช้ interface ชัดเจนเพื่อให้เปลี่ยน provider, storage หรือ UI ได้โดยไม่กระทบส่วนอื่นโดยไม่จำเป็น
