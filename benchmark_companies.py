import tsaa_awards

BENCHMARK_COMPANIES = {
    "電子科技": [
        "台積電", "日月光投控", "元太科技", 
        "鴻海精密", "矽品精密工業", "欣興電子"
    ],
    "金融保險": [
        "玉山金控", "中國信託銀行", "國泰金控",
        "台北富邦銀行", "合作金庫銀行", "第一銀行",
        "彰化銀行", "台新金控"
    ],
    "傳統製造": [
        "亞洲水泥", "遠東新世紀", "榮成紙業",
        "宏遠興業", "中鋼公司"
    ],
    "食品零售": [
        "統一超商", "全家便利商店", 
        "全聯實業", "遠東SOGO"
    ],
    "能源公用": [
        "台電公司", "台灣中油",
        "永豐銀行", "崇越科技"
    ],
    "科技製造": [
        "長榮航空", "台糖公司",
        "大愛感恩科技", "佳世達集團"
    ],
    "保險": [
        "富邦產險", "新光人壽", "南山產物"
    ]
}

COMPANY_INFO = {
    "台積電": {
        "產業": "電子科技",
        "股票代號": "2330",
        "ESG報告書URL": "https://esg.tsmc.com/zh-TW/download/sustainabilityReport",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台積電", [])
    },
    "日月光投控": {
        "產業": "電子科技",
        "股票代號": "3711",
        "ESG報告書URL": "https://esg.aseglobal.com",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("日月光投控", [])
    },
    "元太科技": {
        "產業": "電子科技",
        "股票代號": "8069",
        "ESG報告書URL": "https://www.eink.com/esg.html",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("元太科技", [])
    },
    "鴻海精密": {
        "產業": "電子科技",
        "股票代號": "2317",
        "ESG報告書URL": "https://esg.foxconn.com",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("鴻海精密", [])
    },
    "矽品精密工業": {
        "產業": "電子科技",
        "股票代號": "2325",
        "ESG報告書URL": "https://www.spil.com.tw/sustainability/",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("矽品精密工業", [])
    },
    "欣興電子": {
        "產業": "電子科技",
        "股票代號": "3037",
        "ESG報告書URL": "https://www.unimicron.com/tw/csr/",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("欣興電子", [])
    },
    "玉山金控": {
        "產業": "金融保險",
        "股票代號": "2884",
        "ESG報告書URL": "https://www.esunfhc.com/zh-tw/sustainability",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("玉山金控", [])
    },
    "中國信託銀行": {
        "產業": "金融保險",
        "股票代號": "2891",
        "ESG報告書URL": "https://www.ctbcbank.com/content/dam/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("中國信託銀行", [])
    },
    "國泰金控": {
        "產業": "金融保險",
        "股票代號": "2882",
        "ESG報告書URL": "https://www.cathayholdings.com/holdings/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("國泰金控", [])
    },
    "台北富邦銀行": {
        "產業": "金融保險",
        "股票代號": "2881",
        "ESG報告書URL": "https://www.fubon.com/finance/home/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台北富邦銀行", [])
    },
    "合作金庫銀行": {
        "產業": "金融保險",
        "股票代號": "5880",
        "ESG報告書URL": "https://www.tcb-bank.com.tw/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("合作金庫銀行", [])
    },
    "第一銀行": {
        "產業": "金融保險",
        "股票代號": "2892",
        "ESG報告書URL": "https://www.firstbank.com.tw/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("第一銀行", [])
    },
    "彰化銀行": {
        "產業": "金融保險",
        "股票代號": "2801",
        "ESG報告書URL": "https://www.bankchb.com/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("彰化銀行", [])
    },
    "台新金控": {
        "產業": "金融保險",
        "股票代號": "2887",
        "ESG報告書URL": "https://www.taishinholdings.com.tw/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台新金控", [])
    },
    "亞洲水泥": {
        "產業": "傳統製造",
        "股票代號": "1102",
        "ESG報告書URL": "https://www.acc.com.tw/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("亞洲水泥", [])
    },
    "遠東新世紀": {
        "產業": "傳統製造",
        "股票代號": "1402",
        "ESG報告書URL": "https://www.fenc.com/sustainability",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("遠東新世紀", [])
    },
    "榮成紙業": {
        "產業": "傳統製造",
        "股票代號": "1909",
        "ESG報告書URL": "https://www.longchen.com.tw/csr/",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("榮成紙業", [])
    },
    "宏遠興業": {
        "產業": "傳統製造",
        "股票代號": "1460",
        "ESG報告書URL": "https://www.everest.com.tw/zh/sustainability",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("宏遠興業", [])
    },
    "中鋼公司": {
        "產業": "傳統製造",
        "股票代號": "2002",
        "ESG報告書URL": "https://www.csc.com.tw/csc/hr/csr/",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("中鋼公司", [])
    },
    "統一超商": {
        "產業": "食品零售",
        "股票代號": "2912",
        "ESG報告書URL": "https://www.7-11.com.tw/company/esg/reports.aspx",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("統一超商", [])
    },
    "全家便利商店": {
        "產業": "食品零售",
        "股票代號": "5903",
        "ESG報告書URL": "https://www.family.com.tw/sustainability",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("全家便利商店", [])
    },
    "全聯實業": {
        "產業": "食品零售",
        "股票代號": "2913",
        "ESG報告書URL": "https://www.pxmart.com.tw/px/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("全聯實業", [])
    },
    "遠東SOGO": {
        "產業": "食品零售",
        "股票代號": "2908",
        "ESG報告書URL": "https://www.sogo.com.tw/CSR/",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("遠東SOGO", [])
    },
    "台電公司": {
        "產業": "能源公用",
        "股票代號": "",
        "ESG報告書URL": "https://www.taipower.com.tw/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台電公司", [])
    },
    "台灣中油": {
        "產業": "能源公用",
        "股票代號": "",
        "ESG報告書URL": "https://www.cpc.com.tw/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台灣中油", [])
    },
    "永豐銀行": {
        "產業": "能源公用",
        "股票代號": "2890",
        "ESG報告書URL": "https://www.sinopac.com/SinopacBankWeb/personal/about/esg/",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("永豐銀行", [])
    },
    "崇越科技": {
        "產業": "能源公用",
        "股票代號": "5434",
        "ESG報告書URL": "https://www.tec.com.tw/tw/csr",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("崇越科技", [])
    },
    "長榮航空": {
        "產業": "科技製造",
        "股票代號": "2618",
        "ESG報告書URL": "https://esg.evaair.com",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("長榮航空", [])
    },
    "台糖公司": {
        "產業": "科技製造",
        "股票代號": "1702",
        "ESG報告書URL": "https://www.taisugar.com.tw/chinese/CP2.aspx?n=10528",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台糖公司", [])
    },
    "大愛感恩科技": {
        "產業": "科技製造",
        "股票代號": "2464",
        "ESG報告書URL": "https://www.daait.com/aboutus/report.php",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("大愛感恩科技", [])
    },
    "佳世達集團": {
        "產業": "科技製造",
        "股票代號": "2352",
        "ESG報告書URL": "https://www.qisda.com/tw/Sustainability",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("佳世達集團", [])
    },
    "富邦產險": {
        "產業": "保險",
        "股票代號": "2850",
        "ESG報告書URL": "https://www.fubon.com/insurance/home/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("富邦產險", [])
    },
    "新光人壽": {
        "產業": "保險",
        "股票代號": "2888",
        "ESG報告書URL": "https://www.skl.com.tw/about/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("新光人壽", [])
    },
    "南山產物": {
        "產業": "保險",
        "股票代號": "2867",
        "ESG報告書URL": "https://www.nanshaninsurance.com.tw/NanshanWeb/about/esg",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("南山產物", [])
    },
    # P1 新增公司
    "聯發科": {
        "產業": "電子科技",
        "股票代號": "2454",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("聯發科", [])
    },
    "兆豐金": {
        "產業": "金融保險",
        "股票代號": "2886",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("兆豐金", [])
    },
    "統一": {
        "產業": "食品零售",
        "股票代號": "1216",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("統一", [])
    },
    "大立光": {
        "產業": "電子科技",
        "股票代號": "3008",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("大立光", [])
    },
    "華碩": {
        "產業": "電子科技",
        "股票代號": "2357",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("華碩", [])
    },
    "元大金": {
        "產業": "金融保險",
        "股票代號": "2885",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("元大金", [])
    },
    "長榮": {
        "產業": "科技製造",
        "股票代號": "2603",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("長榮", [])
    },
    "南亞": {
        "產業": "傳統製造",
        "股票代號": "1303",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("南亞", [])
    },
    "華南金": {
        "產業": "金融保險",
        "股票代號": "2880",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("華南金", [])
    },
    "聯詠": {
        "產業": "電子科技",
        "股票代號": "3034",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("聯詠", [])
    },
    "瑞昱": {
        "產業": "電子科技",
        "股票代號": "2379",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("瑞昱", [])
    },
    "台泥": {
        "產業": "傳統製造",
        "股票代號": "1101",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台泥", [])
    },
    "緯創": {
        "產業": "電子科技",
        "股票代號": "3231",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("緯創", [])
    },
    "英業達": {
        "產業": "電子科技",
        "股票代號": "2356",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("英業達", [])
    },
    "遠傳": {
        "產業": "電信",
        "股票代號": "4904",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("遠傳", [])
    },
    "台灣大": {
        "產業": "電信",
        "股票代號": "3045",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台灣大", [])
    },
    "台化": {
        "產業": "傳統製造",
        "股票代號": "1326",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台化", [])
    },
    "台塑化": {
        "產業": "能源公用",
        "股票代號": "6505",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("台塑化", [])
    },
    "陽明": {
        "產業": "科技製造",
        "股票代號": "2609",
        "ESG報告書URL": "待補充",
        "TSAA獎項": tsaa_awards.TSAA_AWARDS.get("陽明", [])
    }
}

if __name__ == "__main__":
    # 統計和輸出
    total_companies = sum(len(companies) for companies in BENCHMARK_COMPANIES.values())
    print(f"總公司數量: {total_companies}")

    print("各產業分布:")
    for industry, companies in BENCHMARK_COMPANIES.items():
        print(f"{industry}: {len(companies)} 家")

    companies_with_awards = [company for company, info in COMPANY_INFO.items() if info["TSAA獎項"]]
    print(f"有TSAA得獎記錄的公司: {companies_with_awards}")
    print(f"總得獎公司數: {len(companies_with_awards)}")

    award_counts = {company: len(info["TSAA獎項"]) for company, info in COMPANY_INFO.items() if info["TSAA獎項"]}
    sorted_awards = sorted(award_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    print("每家公司得獎數量排名top10:")
    for company, count in sorted_awards:
        print(f"{company}: {count} 項")

    companies_with_url = [company for company, info in COMPANY_INFO.items() if info["ESG報告書URL"] and info["ESG報告書URL"] != "待補充"]
    print(f"有URL的公司: {len(companies_with_url)} 家")

    pending = [company for company, info in COMPANY_INFO.items() if info["ESG報告書URL"] == "待補充"]
    print(f"待補充: {len(pending)} 家")