"""
app/core/company_resolver.py
Enterprise Company Resolver v2
"""

import re
from rapidfuzz import process, fuzz
from opencc import OpenCC

cc = OpenCC('t2s')

COMPANY_MASTER = {
    "台積電": {
        "stock_id": "2330",
        "group": "台積電",
        "aliases": ["台積", "TSMC", "Taiwan Semiconductor", "台灣積體電路", "2330"]
    },
    "中國信託銀行": {
        "stock_id": None,
        "group": "中信集團",
        "aliases": ["中信", "中信銀", "中國信託", "CTBC", "CTBC Bank"]
    },
    "中華電信": {
        "stock_id": "2412",
        "group": "中華電信",
        "aliases": ["中華電", "Chunghwa Telecom", "CHT", "2412"]
    },
    "中鋼公司": {
        "stock_id": "2002",
        "group": "中鋼集團",
        "aliases": ["中鋼", "China Steel", "2002"]
    },
    "亞洲水泥": {
        "stock_id": "1102",
        "group": "遠東集團",
        "aliases": ["亞泥", "Asia Cement", "1102"]
    },
    "佳世達集團": {
        "stock_id": "2352",
        "group": "佳世達集團",
        "aliases": ["佳世達", "Qisda", "2352"]
    },
    "南山產物": {
        "stock_id": None,
        "group": "南山集團",
        "aliases": ["南山", "南山產物保險", "Nan Shan"]
    },
    "台北富邦銀行": {
        "stock_id": None,
        "group": "富邦集團",
        "aliases": ["富邦銀行", "台北富邦", "富邦銀", "Taipei Fubon Bank"]
    },
    "台塑": {
        "stock_id": "1301",
        "group": "台塑集團",
        "aliases": ["台塑化", "Formosa Plastics", "FPC", "1301"]
    },
    "台新金控": {
        "stock_id": "2887",
        "group": "台新集團",
        "aliases": ["台新", "台新金", "台新新光金", "台新新光金控", "Taishin", "2887"]
    },
    "台新銀行": {
        "stock_id": None,
        "group": "台新集團",
        "aliases": ["台新銀", "Taishin Bank"]
    },
    "台灣中油": {
        "stock_id": None,
        "group": "台灣中油",
        "aliases": ["中油", "CPC", "台灣中油公司"]
    },
    "台達電": {
        "stock_id": "2308",
        "group": "台達電集團",
        "aliases": ["台達", "Delta Electronics", "2308"]
    },
    "合作金庫銀行": {
        "stock_id": "5880",
        "group": "合庫集團",
        "aliases": ["合庫", "合作金庫", "TCB", "5880"]
    },
    "國泰金控": {
        "stock_id": "2882",
        "group": "國泰集團",
        "aliases": ["國泰", "國泰金", "Cathay", "Cathay Financial", "2882"]
    },
    "宏遠興業": {
        "stock_id": "1460",
        "group": "宏遠集團",
        "aliases": ["宏遠", "Everest Textile", "1460"]
    },
    "崇越科技": {
        "stock_id": "5434",
        "group": "崇越集團",
        "aliases": ["崇越", "Topco Technologies", "5434"]
    },
    "廣達": {
        "stock_id": "2382",
        "group": "廣達集團",
        "aliases": ["廣達電腦", "Quanta", "Quanta Computer", "2382"]
    },
    "彰化銀行": {
        "stock_id": "2801",
        "group": "彰化銀行",
        "aliases": ["彰銀", "Chang Hwa Bank", "2801"]
    },
    "日月光投控": {
        "stock_id": "3711",
        "group": "日月光集團",
        "aliases": ["日月光", "ASE", "ASE Technology", "3711"]
    },
    "榮成紙業": {
        "stock_id": "1909",
        "group": "榮成集團",
        "aliases": ["榮成", "Yuen Foong Yu", "1909"]
    },
    "欣興電子": {
        "stock_id": "3037",
        "group": "欣興集團",
        "aliases": ["欣興", "Unimicron", "3037"]
    },
    "永豐銀行": {
        "stock_id": "2890",
        "group": "永豐金集團",
        "aliases": ["永豐", "永豐金", "SinoPac", "Bank SinoPac", "2890"]
    },
    "玉山金控": {
        "stock_id": "2884",
        "group": "玉山集團",
        "aliases": ["玉山", "玉山金", "E.SUN", "E.SUN Financial", "2884"]
    },
    "第一銀行": {
        "stock_id": "2892",
        "group": "第一金集團",
        "aliases": ["一銀", "第一金", "First Bank", "First Financial", "2892"]
    },
    "統一超商": {
        "stock_id": "2912",
        "group": "統一集團",
        "aliases": ["統一", "7-11", "7-ELEVEN", "統一超", "President Chain Store", "2912"]
    },
    "聯電": {
        "stock_id": "2303",
        "group": "聯電集團",
        "aliases": ["UMC", "United Microelectronics", "2303"]
    },
    "遠東新世紀": {
        "stock_id": "1402",
        "group": "遠東集團",
        "aliases": ["遠東", "遠東新", "Far Eastern New Century", "1402"]
    },
    "長榮航空": {
        "stock_id": "2618",
        "group": "長榮集團",
        "aliases": ["長榮", "EVA Air", "EVA Airways", "2618"]
    },
    "開發金控": {
        "stock_id": "2883",
        "group": "開發金集團",
        "aliases": ["開發金", "CDIB", "China Development Financial", "2883"]
    },
    "鴻海精密": {
        "stock_id": "2317",
        "group": "鴻海集團",
        "aliases": ["鴻海", "Foxconn", "Hon Hai", "2317"]
    },
    "聯發科": {
        "stock_id": "2454",
        "group": "聯發科",
        "aliases": ["MediaTek", "2454"],
    },
    "兆豐金": {
        "stock_id": "2886",
        "group": "兆豐金集團",
        "aliases": ["兆豐金控", "兆豐銀行", "Mega Financial", "2886"],
    },
    "統一": {
        "stock_id": "1216",
        "group": "統一集團",
        "aliases": ["統一企業", "Uni-President", "1216"],
    },
    "大立光": {
        "stock_id": "3008",
        "group": "大立光",
        "aliases": ["Largan", "3008"],
    },
    "華碩": {
        "stock_id": "2357",
        "group": "華碩集團",
        "aliases": ["ASUS", "2357"],
    },
    "元大金": {
        "stock_id": "2885",
        "group": "元大集團",
        "aliases": ["元大金控", "Yuanta Financial", "2885"],
    },
    "長榮": {
        "stock_id": "2603",
        "group": "長榮集團",
        "aliases": ["長榮海運", "Evergreen Marine", "2603"],
    },
    "南亞": {
        "stock_id": "1303",
        "group": "台塑集團",
        "aliases": ["南亞塑膠", "Nan Ya Plastics", "1303"],
    },
    "華南金": {
        "stock_id": "2880",
        "group": "華南金集團",
        "aliases": ["華南金控", "華南銀行", "Hua Nan Financial", "2880"],
    },
    "聯詠": {
        "stock_id": "3034",
        "group": "聯詠",
        "aliases": ["Novatek", "3034"],
    },
    "瑞昱": {
        "stock_id": "2379",
        "group": "瑞昱",
        "aliases": ["Realtek", "2379"],
    },
    "台泥": {
        "stock_id": "1101",
        "group": "台泥集團",
        "aliases": ["台灣水泥", "Taiwan Cement", "1101"],
    },
    "緯創": {
        "stock_id": "3231",
        "group": "緯創集團",
        "aliases": ["Wistron", "3231"],
    },
    "英業達": {
        "stock_id": "2356",
        "group": "英業達集團",
        "aliases": ["Inventec", "2356"],
    },
    "遠傳": {
        "stock_id": "4904",
        "group": "遠傳集團",
        "aliases": ["遠傳電信", "FarEasTone", "4904"],
    },
    "台灣大": {
        "stock_id": "3045",
        "group": "台灣大哥大集團",
        "aliases": ["台灣大哥大", "Taiwan Mobile", "TWM", "3045"],
    },
    "台化": {
        "stock_id": "1326",
        "group": "台塑集團",
        "aliases": ["台灣化學纖維", "Formosa Chemicals", "1326"],
    },
    "台塑化": {
        "stock_id": "6505",
        "group": "台塑集團",
        "aliases": ["台塑石化", "FPCC", "6505"],
    },
    "陽明": {
        "stock_id": "2609",
        "group": "陽明集團",
        "aliases": ["陽明海運", "Yang Ming Marine", "2609"],
    },
    "元太科技": {
        "stock_id": "8069",
        "group": "元太科技",
        "aliases": ["E Ink", "元太", "8069"],
    },
    "全家便利商店": {
        "stock_id": "5903",
        "group": "全家集團",
        "aliases": ["全家", "FamilyMart", "5903"],
    },
    "仁寶": {
        "stock_id": "2324",
        "group": "仁寶集團",
        "aliases": ["仁寶電腦", "Compal", "2324"],
    },
    "鴻準": {
        "stock_id": "2354",
        "group": "鴻海集團",
        "aliases": ["Foxconn Precision", "2354"],
    },
    "群光": {
        "stock_id": "2385",
        "group": "群光集團",
        "aliases": ["Chicony", "2385"],
    },
    "南亞科": {
        "stock_id": "2408",
        "group": "台塑集團",
        "aliases": ["南亞科技", "Nanya Technology", "2408"],
    },
    "友達": {
        "stock_id": "2409",
        "group": "友達集團",
        "aliases": ["友達光電", "AUO", "2409"],
    },
    "可成": {
        "stock_id": "2474",
        "group": "可成科技",
        "aliases": ["Catcher Technology", "2474"],
    },
    "華航": {
        "stock_id": "2610",
        "group": "華航集團",
        "aliases": ["中華航空", "China Airlines", "CAL", "2610"],
    },
    "台灣高鐵": {
        "stock_id": "2633",
        "group": "台灣高鐵",
        "aliases": ["高鐵", "THSR", "2633"],
    },
    "文曄": {
        "stock_id": "3036",
        "group": "文曄集團",
        "aliases": ["WPG", "3036"],
    },
    "健鼎": {
        "stock_id": "3044",
        "group": "健鼎科技",
        "aliases": ["Tripod Technology", "3044"],
    },
    "群創": {
        "stock_id": "3481",
        "group": "群創集團",
        "aliases": ["群創光電", "Innolux", "3481"],
    },
    "大聯大": {
        "stock_id": "3702",
        "group": "大聯大集團",
        "aliases": ["WPG Holdings", "3702"],
    },
    "力成": {
        "stock_id": "6239",
        "group": "力成科技",
        "aliases": ["Powertech Technology", "6239"],
    },
    "南電": {
        "stock_id": "8046",
        "group": "南亞集團",
        "aliases": ["南亞電路板", "NPC", "8046"],
    },
    "寶成": {
        "stock_id": "9904",
        "group": "寶成集團",
        "aliases": ["Pou Chen", "9904"],
    },
    "豐泰": {
        "stock_id": "9910",
        "group": "豐泰集團",
        "aliases": ["Feng Tay", "9910"],
    },
    "巨大": {
        "stock_id": "9921",
        "group": "巨大集團",
        "aliases": ["捷安特", "Giant", "9921"],
    },
    "奇鋐": {
        "stock_id": "3017",
        "group": "奇鋐科技",
        "aliases": ["Auras Technology", "3017"],
    },
    "光寶科": {
        "stock_id": "2301",
        "group": "光寶集團",
        "aliases": ["光寶科技", "Lite-On", "2301"],
    },
    "和碩": {
        "stock_id": "4938",
        "group": "和碩集團",
        "aliases": ["Pegatron", "4938"],
    },
    "儒鴻": {
        "stock_id": "1476",
        "group": "儒鴻集團",
        "aliases": ["Eclat Textile", "1476"],
    },
    "東元": {
        "stock_id": "1504",
        "group": "東元集團",
        "aliases": ["TECO", "1504"],
    },
    "正新": {
        "stock_id": "2105",
        "group": "正新集團",
        "aliases": ["正新橡膠", "Cheng Shin Rubber", "CST", "2105"],
    },
    "和泰車": {
        "stock_id": "2207",
        "group": "和泰集團",
        "aliases": ["和泰汽車", "Hotai Motor", "2207"],
    },
    "宏碁": {
        "stock_id": "2353",
        "group": "宏碁集團",
        "aliases": ["Acer", "2353"],
    },
    "微星": {
        "stock_id": "2377",
        "group": "微星科技",
        "aliases": ["MSI", "2377"],
    },
    "研華": {
        "stock_id": "2395",
        "group": "研華科技",
        "aliases": ["Advantech", "2395"],
    },
    "臺企銀": {
        "stock_id": "2834",
        "group": "臺企銀",
        "aliases": ["台灣企銀", "Taiwan Business Bank", "2834"],
    },
    "中租": {
        "stock_id": "5871",
        "group": "中租集團",
        "aliases": ["中租-KY", "Chailease", "5871"],
    },
    "上海商銀": {
        "stock_id": "5876",
        "group": "上海商銀",
        "aliases": ["上海商業儲蓄銀行", "Shanghai Commercial Bank", "5876"],
    },
    "群益證": {
        "stock_id": "6005",
        "group": "群益金鼎集團",
        "aliases": ["群益金鼎證券", "Capital Securities", "6005"],
    },
    "國巨": {
        "stock_id": "2327",
        "group": "國巨集團",
        "aliases": ["YAGEO", "2327"],
    },
}

INDUSTRY_GROUPS = {
    "半導體製造": ["台積電", "聯電", "聯發科", "聯詠", "瑞昱", "南亞科"],
    "半導體封測": ["日月光投控", "大立光", "力成"],
    "被動元件": ["國巨"],
    "電子代工": ["鴻海精密", "廣達", "佳世達集團", "緯創", "英業達", "仁寶", "和碩", "鴻準"],
    "電子零組件": ["台達電", "崇越科技", "元太科技", "光寶科", "群光", "奇鋐", "可成", "研華"],
    "PCB電路板": ["欣興電子", "健鼎", "南電"],
    "面板": ["友達", "群創"],
    "金融銀行": ["中國信託銀行", "台北富邦銀行", "玉山金控", "永豐銀行",
                "彰化銀行", "合作金庫銀行", "第一銀行", "華南金",
                "臺企銀", "上海商銀", "台新銀行"],
    "金控": ["開發金控", "國泰金控", "台新金控", "兆豐金", "元大金"],
    "證券": ["群益證"],
    "租賃金融": ["中租"],
    "石化塑化": ["台塑", "台塑化", "台化", "南亞"],
    "能源": ["台灣中油"],
    "鋼鐵": ["中鋼公司"],
    "水泥建材": ["亞洲水泥", "台泥"],
    "紡織": ["宏遠興業", "遠東新世紀", "儒鴻"],
    "運動用品": ["巨大", "寶成", "豐泰"],
    "造紙": ["榮成紙業"],
    "電機機械": ["東元"],
    "汽車": ["和泰車"],
    "橡膠輪胎": ["正新"],
    "電腦品牌": ["宏碁", "微星", "華碩"],
    "流通": ["大聯大", "文曄"],
    "電信": ["中華電信", "遠傳", "台灣大"],
    "航運": ["長榮", "陽明", "長榮航空", "華航"],
    "高鐵": ["台灣高鐵"],
    "零售": ["統一超商", "全家便利商店", "統一"],
    "保險": ["南山產物"],
}

REMOVE_WORDS = [
    "股份有限公司", "有限公司", "公司", "控股", "集團", "企業", "股份",
]

OCR_FIXES = {
    "台枳": "台積",
    "國太": "國泰",
    "富帮": "富邦",
    "中固信託": "中國信託",
    "台新新光全": "台新新光金",
}

# 建立 alias index
ALIAS_INDEX = {}
for standard_name, data in COMPANY_MASTER.items():
    ALIAS_INDEX[standard_name] = standard_name
    for alias in data["aliases"]:
        ALIAS_INDEX[alias] = standard_name


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip().upper()
    text = re.sub(r"\s+", "", text)
    for k, v in OCR_FIXES.items():
        text = text.replace(k.upper(), v.upper())
    text = cc.convert(text)
    for w in REMOVE_WORDS:
        text = text.replace(cc.convert(w.upper()), "")
    return text


def resolve_company(text: str, threshold: int = 72) -> str | None:
    """
    將使用者輸入解析為 MongoDB 實際公司名稱

    Returns:
        標準公司名稱，找不到回傳 None
    """
    if not text:
        return None

    norm_input = normalize_text(text)

    # exact alias
    for alias, standard in ALIAS_INDEX.items():
        if normalize_text(alias) == norm_input:
            return standard

    # fuzzy
    search_pool = {normalize_text(alias): standard for alias, standard in ALIAS_INDEX.items()}
    result = process.extractOne(norm_input, list(search_pool.keys()), scorer=fuzz.WRatio)
    if result:
        matched_norm, score, _ = result
        if score >= threshold:
            return search_pool[matched_norm]

    return None


def resolve_companies_from_query(query: str) -> list[str]:
    """從查詢文字自動偵測公司名稱"""
    found = []
    for alias, standard in ALIAS_INDEX.items():
        if alias in query and standard not in found:
            found.append(standard)
    for company in COMPANY_MASTER:
        if company in query and company not in found:
            found.append(company)
    return found


def get_company_info(standard_name: str) -> dict | None:
    """取得公司完整資訊（stock_id, group, aliases）"""
    return COMPANY_MASTER.get(standard_name)
