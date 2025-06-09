#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.kyujinbox_scraper import KyujinboxScraper
import json

def test_kyujinbox_scraper():
    """修正された求人ボックススクレイパーをテスト"""
    
    print("=== 求人ボックススクレイパー修正版テスト ===\n")
    
    # スクレイパーインスタンス作成
    scraper = KyujinboxScraper()
    
    # テスト条件
    employment_type_word = "1"  # 正社員
    keyword = "看護師"
    area = "東京都"
    max_jobs = 3  # テスト用に少数
    
    print(f"テスト条件:")
    print(f"- 雇用形態: {employment_type_word} (正社員)")
    print(f"- キーワード: {keyword}")
    print(f"- エリア: {area}")
    print(f"- 最大取得数: {max_jobs}")
    print()
    
    # スクレイピング実行
    try:
        results, error = scraper.scrape_jobs(
            employment_type_word=employment_type_word,
            keyword=keyword,
            area=area,
            max_jobs=max_jobs,
            debug_mode=True  # デバッグモード有効
        )
        
        if error:
            print(f"❌ エラー発生: {error}")
            return
        
        if not results:
            print("❌ 結果が取得できませんでした")
            return
        
        print(f"\n✅ 成功！{len(results)}件の求人を取得しました\n")
        
        # 結果の詳細表示
        for i, job in enumerate(results, 1):
            print(f"--- 求人 {i} ---")
            print(f"施設名: {job.get('facility_name', 'N/A')}")
            print(f"代表者: {job.get('representative', 'N/A')}")
            print(f"住所: {job.get('address', 'N/A')}")
            print(f"ウェブサイトURL: {job.get('website_url', 'N/A')}")
            print(f"電話番号: {job.get('phone_number', 'N/A')}")
            print(f"メールアドレス: {job.get('email', 'N/A')}")
            print(f"事業内容: {job.get('business_content', 'N/A')}")
            print(f"詳細ページURL: {job.get('source_url', 'N/A')}")
            print()
        
        # 問題の確認
        print("=== 修正結果の確認 ===")
        youtube_count = sum(1 for job in results if 'youtube' in job.get('website_url', '').lower())
        valid_website_count = sum(1 for job in results if job.get('website_url') and 'youtube' not in job.get('website_url', '').lower() and job.get('website_url') != 'N/A')
        
        print(f"✅ 総取得件数: {len(results)}")
        print(f"❌ YouTubeのWebサイトURL: {youtube_count}件")
        print(f"✅ 有効なWebサイトURL: {valid_website_count}件")
        
        if youtube_count == 0:
            print("\n🎉 YouTube問題が解決されました！")
        else:
            print(f"\n⚠️  まだ{youtube_count}件のYouTube URLが残っています。")
        
        # 詳細ページURLの確認
        jb_url_count = sum(1 for job in results if '/jb/' in job.get('source_url', ''))
        print(f"✅ /jb/ 詳細ページURL: {jb_url_count}件")
        
        if jb_url_count == len(results):
            print("🎉 詳細ページURL問題も解決されました！")
        else:
            print(f"⚠️  /jb/ URLでない詳細ページが{len(results) - jb_url_count}件あります。")
        
        # JSONファイルに保存
        output_file = "kyujinbox_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📁 結果を {output_file} に保存しました")
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kyujinbox_scraper() 