"""Static market universe: index cards, ETF flow groups, breadth stocks."""

from __future__ import annotations

INDICES = [
    {"symbol": "^GSPC", "label": "S&P 500", "short": "S&P 500", "kind": "index"},
    {"symbol": "^IXIC", "label": "NASDAQ", "short": "NASDAQ", "kind": "index"},
    {"symbol": "^DJI", "label": "DOW", "short": "DOW", "kind": "index"},
    {"symbol": "BTC-USD", "label": "BTC", "short": "BTC", "kind": "crypto"},
    {"symbol": "GC=F", "label": "GOLD", "short": "GOLD", "kind": "commodity"},
]

BENCHMARK = {"symbol": "SPY", "name": "S&P 500 (ตลาดรวม)", "name_th": "S&P 500 (ตลาดรวม)"}

GROUP_META = [
    {
        "key": "broad",
        "label": "ภาพใหญ่",
        "description": "ดัชนีและสินทรัพย์หลักที่บอกทิศทางตลาดโดยรวม — หุ้นสหรัฐ, ตลาดเกิดใหม่, พันธบัตร, สินค้าโภคภัณฑ์",
    },
    {
        "key": "sectors",
        "label": "กลุ่มธุรกิจ",
        "description": "11 กลุ่มธุรกิจมาตรฐานของ S&P 500 — เรียงจากแรงซื้อขายของกลุ่มในภาพรวม",
    },
    {
        "key": "industries",
        "label": "หุ้นกลุ่มย่อย",
        "description": "อุตสาหกรรมเฉพาะทางที่มักขับเคลื่อนตลาด เช่น เซมิคอนดักเตอร์ ชีวเทค ซอฟต์แวร์ ค้าปลีก",
    },
    {
        "key": "themes",
        "label": "ธีมและประเทศ",
        "description": "ETF ตามธีมและตลาดต่างประเทศ — จีน อินเดีย ญี่ปุ่น ยุโรป พลังงานสะอาด และนวัตกรรม",
    },
]

GROUPS: dict[str, list[dict]] = {
    "broad": [
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "name_th": "S&P 500 (ตลาดรวม)"},
        {"symbol": "QQQ", "name": "Invesco QQQ Trust", "name_th": "Nasdaq 100"},
        {"symbol": "DIA", "name": "SPDR Dow Jones Industrial Average ETF", "name_th": "ดาวโจนส์"},
        {"symbol": "IWM", "name": "iShares Russell 2000 ETF", "name_th": "หุ้นเล็ก Russell 2000"},
        {"symbol": "RSP", "name": "Invesco S&P 500 Equal Weight ETF", "name_th": "S&P 500 ถ่วงน้ำหนักเท่ากัน"},
        {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "name_th": "ตลาดหุ้นสหรัฐรวม"},
        {"symbol": "EFA", "name": "iShares MSCI EAFE ETF", "name_th": "ตลาดพัฒนาแล้ว (นอกสหรัฐ)"},
        {"symbol": "EEM", "name": "iShares MSCI Emerging Markets ETF", "name_th": "ตลาดเกิดใหม่"},
        {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "name_th": "พันธบัตรรัฐบาล 20 ปี"},
        {"symbol": "HYG", "name": "iShares iBoxx High Yield Corporate Bond ETF", "name_th": "หุ้นกู้ผลตอบแทนสูง"},
        {"symbol": "LQD", "name": "iShares iBoxx Investment Grade Corporate Bond ETF", "name_th": "หุ้นกู้เกรดลงทุน"},
        {"symbol": "GLD", "name": "SPDR Gold Shares", "name_th": "ทองคำ"},
        {"symbol": "SLV", "name": "iShares Silver Trust", "name_th": "เงิน"},
        {"symbol": "GDX", "name": "VanEck Gold Miners ETF", "name_th": "เหมืองทองคำ"},
        {"symbol": "USO", "name": "United States Oil Fund", "name_th": "น้ำมันดิบ"},
        {"symbol": "UUP", "name": "Invesco DB US Dollar Index Fund", "name_th": "ดอลลาร์สหรัฐ"},
        {"symbol": "IBIT", "name": "iShares Bitcoin Trust", "name_th": "บิตคอยน์"},
    ],
    "sectors": [
        {"symbol": "XLK", "name": "Technology Select Sector SPDR", "name_th": "เทคโนโลยี"},
        {"symbol": "XLC", "name": "Communication Services Select Sector SPDR", "name_th": "สื่อสาร"},
        {"symbol": "XLY", "name": "Consumer Discretionary Select Sector SPDR", "name_th": "บริโภคฟุ่มเฟือย"},
        {"symbol": "XLP", "name": "Consumer Staples Select Sector SPDR", "name_th": "บริโภคจำเป็น"},
        {"symbol": "XLE", "name": "Energy Select Sector SPDR", "name_th": "พลังงาน"},
        {"symbol": "XLF", "name": "Financial Select Sector SPDR", "name_th": "การเงิน"},
        {"symbol": "XLV", "name": "Health Care Select Sector SPDR", "name_th": "สุขภาพ"},
        {"symbol": "XLI", "name": "Industrial Select Sector SPDR", "name_th": "อุตสาหกรรม"},
        {"symbol": "XLB", "name": "Materials Select Sector SPDR", "name_th": "วัตถุดิบ"},
        {"symbol": "XLRE", "name": "Real Estate Select Sector SPDR", "name_th": "อสังหาริมทรัพย์"},
        {"symbol": "XLU", "name": "Utilities Select Sector SPDR", "name_th": "สาธารณูปโภค"},
    ],
    "industries": [
        {"symbol": "SMH", "name": "VanEck Semiconductor ETF", "name_th": "เซมิคอนดักเตอร์"},
        {"symbol": "XBI", "name": "SPDR S&P Biotech ETF", "name_th": "ชีวเทค"},
        {"symbol": "IGV", "name": "iShares Expanded Tech-Software ETF", "name_th": "ซอฟต์แวร์"},
        {"symbol": "XPH", "name": "SPDR S&P Pharmaceuticals ETF", "name_th": "เภสัชกรรม"},
        {"symbol": "KRE", "name": "SPDR S&P Regional Banking ETF", "name_th": "ธนาคารภูมิภาค"},
        {"symbol": "XRT", "name": "SPDR S&P Retail ETF", "name_th": "ค้าปลีก"},
        {"symbol": "ITB", "name": "iShares U.S. Home Construction ETF", "name_th": "ก่อสร้างที่อยู่อาศัย"},
        {"symbol": "JETS", "name": "U.S. Global Jets ETF", "name_th": "สายการบิน"},
        {"symbol": "TAN", "name": "Invesco Solar ETF", "name_th": "พลังงานแสงอาทิตย์"},
        {"symbol": "XME", "name": "SPDR S&P Metals & Mining ETF", "name_th": "โลหะและเหมืองแร่"},
        {"symbol": "XOP", "name": "SPDR S&P Oil & Gas Exploration ETF", "name_th": "สำรวจและผลิตน้ำมัน"},
        {"symbol": "IYT", "name": "iShares U.S. Transportation ETF", "name_th": "ขนส่ง"},
        {"symbol": "PEJ", "name": "Invesco Leisure and Entertainment ETF", "name_th": "พักผ่อนและบันเทิง"},
        {"symbol": "HACK", "name": "Amplify Cybersecurity ETF", "name_th": "ไซเบอร์ซีเคียวริตี้"},
        {"symbol": "BOTZ", "name": "Global X Robotics & AI ETF", "name_th": "หุ่นยนต์และ AI"},
        {"symbol": "ARKG", "name": "ARK Genomic Revolution ETF", "name_th": "จีโนมิกส์"},
    ],
    "themes": [
        {"symbol": "KWEB", "name": "KraneShares CSI China Internet ETF", "name_th": "จีนอินเทอร์เน็ต"},
        {"symbol": "FXI", "name": "iShares China Large-Cap ETF", "name_th": "จีนขนาดใหญ่"},
        {"symbol": "INDA", "name": "iShares MSCI India ETF", "name_th": "อินเดีย"},
        {"symbol": "EWJ", "name": "iShares MSCI Japan ETF", "name_th": "ญี่ปุ่น"},
        {"symbol": "EWG", "name": "iShares MSCI Germany ETF", "name_th": "เยอรมนี"},
        {"symbol": "EWU", "name": "iShares MSCI United Kingdom ETF", "name_th": "สหราชอาณาจักร"},
        {"symbol": "EWZ", "name": "iShares MSCI Brazil ETF", "name_th": "บราซิล"},
        {"symbol": "EWT", "name": "iShares MSCI Taiwan ETF", "name_th": "ไต้หวัน"},
        {"symbol": "EWY", "name": "iShares MSCI South Korea ETF", "name_th": "เกาหลีใต้"},
        {"symbol": "EWA", "name": "iShares MSCI Australia ETF", "name_th": "ออสเตรเลีย"},
        {"symbol": "TUR", "name": "iShares MSCI Turkey ETF", "name_th": "ตุรกี"},
        {"symbol": "EIDO", "name": "iShares MSCI Indonesia ETF", "name_th": "อินโดนีเซีย"},
        {"symbol": "VNM", "name": "VanEck Vietnam ETF", "name_th": "เวียดนาม"},
        {"symbol": "ARKK", "name": "ARK Innovation ETF", "name_th": "นวัตกรรม disruptive"},
        {"symbol": "LIT", "name": "Global X Lithium & Battery Tech ETF", "name_th": "ลิเทียมและแบตเตอรี่"},
        {"symbol": "ICLN", "name": "iShares Global Clean Energy ETF", "name_th": "พลังงานสะอาด"},
    ],
}

# Liquid large caps used for the breadth signal (daily, cached 6h).
BREADTH_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX",
    "JPM", "V", "MA", "COST", "WMT", "DIS", "CRM", "ORCL", "INTC", "PLTR",
    "UBER", "BA", "JNJ", "XOM", "KO", "PEP", "MCD", "NKE", "QCOM", "MU",
    "ADBE", "CSCO", "IBM", "TXN", "AMAT", "LRCX", "ARM", "SHOP", "SNOW", "PANW",
    "GS", "MS", "BAC", "WFC", "C", "BLK", "AXP", "SCHW", "UNH", "LLY",
    "PFE", "MRK", "ABBV", "TMO", "ISRG", "CAT", "DE", "GE", "HON", "LMT",
]

RANGE_META = [
    {"key": "1d", "label": "1 วัน"},
    {"key": "1w", "label": "1 สัปดาห์"},
    {"key": "1mo", "label": "1 เดือน"},
    {"key": "3mo", "label": "3 เดือน"},
    {"key": "ytd", "label": "YTD"},
]


def all_etf_symbols() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for items in GROUPS.values():
        for item in items:
            if item["symbol"] not in seen:
                seen.add(item["symbol"])
                out.append(item["symbol"])
    return out
