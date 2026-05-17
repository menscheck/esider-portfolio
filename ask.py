import argparse
import json

from app.services.esg_service import handle_intent_pipeline_query


def load_company_list():
    # 與公司解析/向量查詢使用同一份 company 清單資料
    with open("app/data/company_list.json", "r", encoding="utf-8") as f:
        return json.load(f)


def run_once(query: str) -> dict:
    company_list = load_company_list()
    return handle_intent_pipeline_query(query, company_list)


def main():
    parser = argparse.ArgumentParser(description="Ask ESG pipeline from terminal.")
    parser.add_argument("query", nargs="?", help="User question")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive mode",
    )
    args = parser.parse_args()

    if args.interactive:
        print("Enter your question. Type 'exit' to quit.")
        while True:
            query = input("> ").strip()
            if not query:
                continue
            if query.lower() in {"exit", "quit"}:
                break
            result = run_once(query)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.query:
        parser.error("query is required unless --interactive is used")

    result = run_once(args.query)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
