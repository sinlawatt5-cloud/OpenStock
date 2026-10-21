# OpenStock — ประวัติโครงการ สถานะปัจจุบัน และแผนงานถัดไป

> สรุปสำหรับส่งต่องาน ณ วันที่ 21 ตุลาคม 2026 จาก source, tests, เอกสารใน repository และประวัติการตัดสินใจที่มีอยู่ในบทสนทนา
>
> **อัปเดตล่าสุด:** ฟีเจอร์ Flows risk-on 6 สัญญาณ **implement เสร็จแล้ว** (backend + frontend + tests) — ดูหัวข้อ 8
>
> **ขอบเขตหลักฐาน:** Git history ที่ตรวจได้ใน checkout นี้มี baseline commit เดียว (`ee971eb`) จึงไม่มี commit ย่อยให้เรียงลำดับการพัฒนาทุกฟีเจอร์ย้อนหลัง เอกสารนี้แยกสิ่งที่ตรวจพบในแอปปัจจุบันออกจากข้อสรุป/แผนที่ยืนยันในบทสนทนา และไม่อ้างว่าแผน Flows ได้ถูก implement แล้ว (ดูหัวข้อ 8 สำหรับสถานะล่าสุด)

## 1. สรุปสำหรับผู้รับช่วง

OpenStock เป็นเว็บแดชบอร์ดภาษาไทยสำหรับติดตามตลาดหุ้นสหรัฐ มี FastAPI backend รวบรวมและแคชข้อมูลตลาด และ React frontend สำหรับหน้า Dashboard, Flows, รายละเอียดหุ้น และ Watchlist

- **งานที่มีอยู่ใน baseline:** API และ UI หลักสำหรับภาพรวมตลาด, ETF returns, ข่าว, ข้อมูลหุ้น/กราฟ/แนวรับแนวต้าน และ watchlist แบบเก็บใน browser
- **งานที่ตกลงเป็นลำดับถัดไป:** เพิ่มแผงวิเคราะห์ risk-on จำนวน 6 สัญญาณในหน้า Flows โดยคำนวณจากผลตอบแทนราคา ETF ตามช่วงเวลาที่เลือก
- **ยังไม่ได้ทำ:** การคำนวณ/แสดง 6 สัญญาณและการทดสอบของฟีเจอร์นี้
- **Repository:** branch `main`, remote `https://github.com/sinlawatt5-cloud/OpenStock.git`; baseline ที่ยืนยันก่อนทำรายงานคือ `ee971eb` (`Initialize OpenStock project baseline`)
- **ข้อจำกัดความหมาย:** หน้า Flows ใช้ผลตอบแทนของ ETF เป็น proxy ไม่ได้วัดเงินสดไหลเข้า/ออกกองทุนจริง และไม่ใช่คำแนะนำลงทุน

## 2. ภาพรวมระบบที่มีอยู่

### เทคโนโลยีและการรัน

- **Backend:** Python 3.12+, FastAPI, SQLite สำหรับ cache/ข้อมูลหุ้น และ pytest สำหรับทดสอบ
- **Frontend:** React 19, TypeScript, Vite, TanStack Query, `lightweight-charts`; Vitest สำหรับ unit tests และมี Playwright smoke tests
- **แหล่งข้อมูล:** Yahoo Finance/yfinance เป็นหลัก; Finnhub และ Alpha Vantage ใช้เป็น fallback/แหล่งเสริม; Gemini/OpenRouter เป็น LLM providers แบบ optional สำหรับสรุปข่าว
- **การตั้งค่า:** API keys มาจาก environment; `backend/.env.example` เป็นตัวอย่าง และ local `.env` ไม่ควร commit
- **โหมดข้อมูล:** มี fixture mode สำหรับทดสอบแบบควบคุม/offline และ cache แบบ TTL พร้อมข้อมูล stale ตาม implementation ปัจจุบัน

### ความสามารถ Backend/API

- Market overview: ดัชนี/สินทรัพย์หลัก, SPY เทียบเส้นค่าเฉลี่ย 200 วัน และ market breadth
- Movers: หุ้น gainers, losers และ most active พร้อม fallback ที่คำนวณจากประวัติราคาเมื่อ screener ใช้ไม่ได้
- Flows: ผลตอบแทน ETF ตัวแทนตามช่วงเวลา, หมวดหมู่/โหมดการแสดง, การจัดอันดับและขนาดแท่งสัมพัทธ์ พร้อม SPY benchmark
- News: ข่าวตลาดและข่าวรายบริษัท, deduplication และสรุปด้วย LLM เมื่อกำหนดค่าไว้ พร้อมทางเลือก fallback
- Symbol: quote, history, profile, peers และแนวรับ/แนวต้านที่คำนวณจากโครงสร้างราคา พร้อม pivot method
- Meta: health/configuration, catalog, รายชื่อหุ้น และ symbol search
- Cache: TTL และ stale-while-revalidate เพื่อจำกัดการเรียก provider ซ้ำ

### ความสามารถ Frontend/UI

- **Dashboard:** index cards, market breadth, movers และข่าว/สรุปตลาด
- **Flows:** เลือกมุมมอง/กลุ่ม/ช่วงเวลา ดูผลตอบแทน ETF และแถบเปรียบเทียบ โดยเน้น SPY
- **หน้า Symbol:** กราฟราคาและช่วงเวลา, เปิด/ปิดแนวรับแนวต้าน, สถิติ/ข้อมูลบริษัท, peers และข่าว
- **Watchlist:** เพิ่ม/ลบ/ดูหุ้นที่ติดตาม โดยเก็บรายการใน browser storage
- มี responsive layout และข้อความเตือน/ข้อจำกัดข้อมูลตลาด

> รายการข้างต้นเป็นสรุปความสามารถที่ตรวจพบใน source ไม่ได้หมายความว่าทุก provider หรือทุกเส้นทางข้อมูลได้รับการตรวจ end-to-end ในรอบรายงานนี้

## 3. ประวัติและการตัดสินใจที่ตรวจสอบได้

1. **สร้าง/รวบรวม baseline ของแอป:** source ปัจจุบันประกอบด้วย backend API, frontend pages, data providers, cache, tests และเอกสาร Flow ตามรายการในหัวข้อ 2 ทั้งนี้ Git history ใน checkout นี้เริ่มจาก baseline commit เดียว จึงระบุลำดับก่อนหน้าแบบละเอียดกว่านี้ไม่ได้
2. **บันทึก baseline ขึ้น GitHub:** มีการสร้าง initial commit `ee971eb` ชื่อ `Initialize OpenStock project baseline` บน `main` และ push ไปยัง `origin/main`
3. **ตรวจสอบ baseline:** ผลที่บันทึกจากรอบก่อนหน้า: backend tests 27 ผ่าน, frontend unit tests 8 ผ่าน และ frontend build สำเร็จ โดยมีคำเตือน bundle size; Playwright smoke tests มีอยู่ แต่ไม่มีหลักฐานว่ารันผ่านในรอบนั้น ดูรายละเอียดในหัวข้อ 6
4. **วิเคราะห์ภาพอ้างอิง Flows:** พบว่าตาราง Flows ปัจจุบันแสดงการเปลี่ยนแปลงของราคา ETF ตัวแทน ไม่ได้แสดงเงินสดไหลเข้าจริง
5. **ยืนยันขอบเขตฟีเจอร์:** ผู้ใช้ตกลงให้เพิ่มแผงสรุป risk-on 6 สัญญาณ อนุมานสูตรจากภาพ reference ใช้ผลตอบแทนในช่วงเวลาเดียวกับที่เลือก และคง theme สีเดิมของแอป ไม่เปลี่ยนเป็น dark theme
6. **บันทึกข้อกำหนดก่อนลงมือ:** มี [เอกสารวิเคราะห์ภาพอ้างอิง Flows](flows-reference-analysis.md) ระบุสูตร, เงื่อนไขข้อมูลไม่ครบ, ขอบเขตหน้าตา และสถานะว่าเป็นงานที่รอ implementation
7. **สถานะล่าสุดก่อนรายงานนี้:** ไม่มีการเปลี่ยน application code เพื่อทำ 6 สัญญาณ; งานที่ทำในรอบสรุปนี้คือจัดทำเอกสารสถานะ/แผนเท่านั้น

## 4. แผนฟีเจอร์ที่ได้รับการยืนยัน: Flows risk-on 6 สัญญาณ

คำนวณผลตอบแทนของ ETF ในช่วงเวลาที่ผู้ใช้เลือก โดยใช้ช่วงและวิธีเดียวกับผลตอบแทนแถว ETF บนหน้า Flows แล้วประเมินเกณฑ์ต่อไปนี้:

| # | ความหมาย | นับเป็นสัญญาณบวกเมื่อ |
|---|---|---|
| 1 | หุ้นเล็กนำตลาด | `return(IWM) - return(SPY) > 0` |
| 2 | หุ้นถ่วงน้ำหนักเท่ากันชนะตลาดรวม | `return(RSP) - return(SPY) > 0` |
| 3 | เครดิตผลตอบแทนสูงนำเครดิตเกรดลงทุน | `return(HYG) - return(LQD) > 0` |
| 4 | ตลาดเกิดใหม่ชนะตลาดรวม | `return(EEM) - return(SPY) > 0` |
| 5 | ดอลลาร์อ่อน | `return(UUP) < 0` |
| 6 | ทองคำแพ้ตลาดรวม/ไม่มี relative outperformance | `return(GLD) - return(SPY) < 0` |

### กติกาผลลัพธ์และการนำเสนอ

- แสดงคะแนนรวมตาม reference เป็น `n/6` และแสดงสถานะ/คำอธิบายของแต่ละสัญญาณ
- ใช้เกณฑ์ strict `> 0` และ `< 0`; ค่าเท่ากับศูนย์ไม่ผ่านเกณฑ์บวก
- สัญญาณที่ขาด ETF หรือมีแท่งราคาไม่พอให้เป็น “ข้อมูลไม่พร้อม” ไม่เดาผลเป็นบวกหรือลบ
- ใช้ช่วงเวลาเดียวกับ filter ที่ผู้ใช้เลือก และให้แผงปรากฏตามมุมมองที่ระบุใน reference (ภาพใหญ่/ทั้งหมด)
- คง theme และตัวกรองเดิม; ระบุชัดว่าเป็นการประมาณจาก **การเคลื่อนไหวของราคา ETF** ไม่ใช่ fund flow หรือคำแนะนำลงทุน
- ETF ที่ต้องใช้ (IWM, SPY, RSP, HYG, LQD, EEM, UUP, GLD) มีอยู่ใน universe ปัจจุบันแล้ว จึงไม่คาดว่าต้องเพิ่ม provider สำหรับขอบเขตนี้

## 5. งานถัดไปตามลำดับแผน

### ขั้นที่ 1 — Backend calculation และ tests

1. อ่านวิธีคำนวณ return/การเลือกช่วงเวลาใน Flows ปัจจุบัน และ reuse ข้อมูล/cache ที่มีอยู่
2. เพิ่มการคำนวณสัญญาณทั้งหก พร้อม label/รายละเอียด, สถานะ availability และ aggregate `n/6`
3. ตัดสิน denominator ให้ไม่ทำให้ข้อมูลขาดดูเหมือนครบ: แสดง unavailable ต่อข้อ และอธิบายคะแนนเมื่อมีข้อมูลไม่ครบตามข้อกำหนดที่ยืนยัน
4. เพิ่ม pytest ครอบคลุม:
   - แต่ละสูตรให้ผลบวก/ไม่บวกตามค่าที่กำหนด
   - ค่าเท่ากับ threshold/ผลตอบแทนเสมอกัน
   - ใช้ช่วงเวลาที่ร้องขอเดียวกับแถว Flows
   - ETF หาย, bars ไม่พอ หรือราคาอ้างอิงไม่ถูกต้อง
   - คะแนนรวมไม่นับสัญญาณ unavailable เป็นผ่าน

### ขั้นที่ 2 — Frontend panel และ interaction tests

1. เพิ่ม/แก้ response types ให้ตรง backend
2. เพิ่มแผง risk-on ในหน้า Flows พร้อม `n/6`, สถานะรายข้อ และ unavailable state
3. เชื่อมกับ filter ช่วงเวลาและมุมมองที่เกี่ยวข้อง โดยไม่ทำให้ผลจากช่วงเก่าค้างเมื่อเปลี่ยน filter
4. คง theme ปัจจุบัน พร้อมข้อความช่วยตีความว่าเป็น price-based proxy
5. เพิ่ม component/interaction tests และ Playwright coverage สำหรับการแสดงผล, เปลี่ยนช่วงเวลา/กลุ่ม, ข้อมูลไม่ครบ, loading/error

### ขั้นที่ 3 — Verification และ preview

- รัน backend pytest, frontend Vitest, build/lint ที่ project รองรับ และ e2e ที่เกี่ยวข้อง
- ทดสอบสูตรด้วย fixture ที่ผลคาดหมายแน่นอนก่อนใช้ข้อมูลตลาดจริง
- เปิดหน้า Flows ใน dev preview ตรวจ desktop/mobile, loading/error, unavailable state และ console/network
- บันทึก warnings/ข้อจำกัด และยืนยันว่าข้อความ/คะแนนไม่สื่อว่าเป็นกระแสเงินสดจริง

### ขั้นที่ 4 — Integration

- หลัง implementation และ verification ผ่าน ค่อย commit/push เมื่อผู้ใช้อนุญาตในรอบนั้น
- ไม่มีคำขอ deploy แอปในแผนนี้; ไม่ควร deploy โดยอนุมานจากคำขอ commit/push

## 6. ผลทดสอบที่มีหลักฐานจากรอบก่อน

ผลต่อไปนี้เป็นผลจาก baseline ก่อนเพิ่มฟีเจอร์ 6 สัญญาณ ไม่ใช่การตรวจ implementation ของแผน Flows ที่ยังไม่เกิดขึ้น:

- Backend: `uv run --locked --group dev pytest` — **27 passed**, มี 1 deprecation warning จาก Starlette/httpx TestClient
- Frontend unit tests: `pnpm test` — **8 passed**
- Frontend build: `pnpm build` — สำเร็จ; มี advisory ว่า JavaScript bundle ใหญ่กว่า 500 kB
- E2E: มี `frontend/e2e/smoke.spec.ts` แต่ไม่มีหลักฐานยืนยันว่ารันผ่านในการตรวจ baseline ดังกล่าว

ผลเหล่านี้เป็นผลที่บันทึกจากรอบก่อน ไม่ใช่การรันใหม่ในงานเขียนรายงานนี้

## 7. ข้อจำกัดและการดูแล repository

- ข้อมูลจาก provider ฟรีอาจล่าช้า ขาดช่วง หรือมีจำนวนแท่งไม่เท่ากัน
- การเทียบ ETF ต้องใช้กรอบเวลาและจุดอ้างอิงที่สอดคล้องกัน
- ห้ามแปลงข้อมูลที่ไม่ครบเป็นคะแนนผ่าน/ไม่ผ่านโดยไม่มีหลักฐาน
- ไฟล์ secrets, ฐานข้อมูล local, logs, build artifacts และ `.freebuff/project-id` เป็นข้อมูล local/metadata ไม่ควรใส่ใน commit
- รายงานนี้เป็น status/handoff ไม่ใช่ข้อกำหนดให้ deploy หรือเปลี่ยน provider

## 8. สถานะล่าสุด: Flows risk-on 6 สัญญาณ (implement เสร็จแล้ว)

ฟีเจอร์ตามหัวข้อ 4–5 **implement เสร็จครบทั้ง backend และ frontend** ในรอบงานล่าสุด (ยังไม่ได้ commit/push)

### ไฟล์ที่เปลี่ยน

| ไฟล์ | การเปลี่ยนแปลง |
|---|---|
| `backend/app/services/flows.py` | เพิ่ม `RISK_ON_PAIRS`, `_ret_for`, `build_risk_signals` และ field `riskOn` ใน response ของ `get_flows` |
| `backend/tests/test_flows.py` | เพิ่ม 7 เคส: สูตรครบทั้ง 6 ข้อ, ผลตอบแทนเสมอกัน, ETF หาย, bars ไม่พอ, ใช้ range เดียวกับแถว Flows, รูปแบบ payload |
| `frontend/src/lib/types.ts` | เพิ่ม `RiskSignal`, `RiskSignalStatus`, `RiskOnSummary` และ `riskOn?` ใน `FlowsResponse` |
| `frontend/src/features/flows/RiskOnPanel.tsx` | component แผงใหม่ (คะแนน `n/6`, สถานะรายสัญญาณ, ข้อความ price-based proxy) |
| `frontend/src/features/flows/RiskOnPanel.test.tsx` | component tests 5 เคส (jsdom + @testing-library/react) |
| `frontend/src/pages/FlowsPage.tsx` | แสดงแผงเมื่อมุมมองเป็น `broad` หรือ `all` |
| `frontend/src/styles/index.css` | สไตล์แผงใหม่ โดยใช้ CSS variables เดิม (`--up`, `--down`, `--up-soft`) ไม่เปลี่ยนธีม |
| `frontend/e2e/smoke.spec.ts` | เพิ่มเคสตรวจแผงบนหน้า Flows + แก้เคสเดิมที่ผูกกับสภาวะตลาดจริง |
| `frontend/vitest.config.ts`, `frontend/package.json` | รองรับไฟล์ test `.tsx` และเพิ่ม devDependencies (`jsdom`, `@testing-library/react`) |

### ผลตรวจสอบที่รันจริงในรอบนี้

- Backend: `uv run --locked --group dev pytest` — **34 passed** (27 เดิม + 7 ใหม่), 1 deprecation warning จาก Starlette/httpx TestClient
- Frontend unit tests: `vitest run` — **13 passed** (8 เดิม + 5 ใหม่)
- Frontend build: `vite build` — สำเร็จ; ยังมี advisory เรื่อง bundle > 500 kB เหมือนเดิม
- Lint: `oxlint` — 3 warnings, 0 errors (ทั้งหมดอยู่ใน `DashboardPage.tsx` และ `SearchDialog.tsx` เดิม ไม่เกี่ยวกับฟีเจอร์นี้)
- E2E: `playwright test` — **6 passed** (5 เดิม + 1 ใหม่) รวมถึงเคสตรวจแผง risk-on
- ตรวจจริงกับข้อมูล live (Yahoo): หน้า Flows แสดงคะแนน `3/6` ตรงกับ API, ไม่มี console error, ไม่ล้นบน viewport มือถือ 390px
- แผงแสดงเฉพาะมุมมอง `broad` และ `all`; ทุกช่วงเวลา (1d/1w/1mo/3mo/ytd) คำนวณคะแนนใหม่ตามช่วงที่เลือก

### หมายเหตุด้านสภาพแวดล้อม

- `pnpm install`/`pnpm add` ในเครื่องนี้ติด supply-chain policy `minimumReleaseAge` ของ pnpm เนื่องจาก `lucide-react@1.61.0` และ `vite@8.3.5` ใน lockfile ถูกปล่อยภายใน 24 ชั่วโมง ต้องใช้ `--config.minimumReleaseAge=0` เฉพาะตอนติดตั้งเท่านั้น (ไม่ได้แก้ config ถาวรของเครื่อง)
- เนื่องจาก policy นี้ `pnpm run <script>` จะพยายามตรวจ dependency ใหม่และล้มเหลว ให้เรียก binary ใน `node_modules/.bin` โดยตรงแทน หรือรัน `pnpm install --config.minimumReleaseAge=0` ก่อน

### ข้อควรระวัง

- แผงนี้เป็นการประมาณภาวะ risk-on จาก **การเคลื่อนไหวของราคา ETF** ไม่ใช่การวัดกระแสเงินสดจริง และไม่ใช่คำแนะนำลงทุน
- สัญญาณที่ข้อมูลไม่พร้อมจะแสดงเป็น “ข้อมูลไม่พร้อม” และ **ไม่ถูกนับเป็นผ่าน** รวมถึงไม่ถูกนับในคะแนน `n/6`
- ยังไม่ได้ commit/push — ต้องได้รับอนุญาตจากผู้ใช้ก่อน
