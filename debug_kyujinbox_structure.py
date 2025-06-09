#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import json

def debug_kyujinbox_structure():
    """求人ボックスの実際のHTML構造を調査"""
    
    # セッション作成
    session = requests.Session()
    
    # ヘッダー設定
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    base_url = "https://xn--pckua2a7gp15o89zb.com"
    
    print("=== 求人ボックス構造調査 ===\n")
    
    # 1. トップページの調査
    print("1. トップページの調査")
    try:
        response = session.get(base_url, headers=headers, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"✅ トップページ取得成功 (サイズ: {len(response.content)} bytes)")
            
            # 雇用形態の選択肢を確認
            employment_selects = soup.find_all('select')
            for i, select in enumerate(employment_selects):
                if 'employment' in str(select).lower() or 'job' in str(select).lower():
                    print(f"雇用形態セレクト {i+1}: {select.get('name', 'no-name')}")
                    options = select.find_all('option')
                    for j, option in enumerate(options[:5]):
                        print(f"  Option {j+1}: value='{option.get('value')}', text='{option.get_text(strip=True)}'")
            
            # フォーム要素を確認
            forms = soup.find_all('form')
            print(f"\nフォーム数: {len(forms)}")
            for i, form in enumerate(forms):
                print(f"Form {i+1}: action='{form.get('action')}', method='{form.get('method')}'")
        else:
            print(f"❌ トップページ取得失敗: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ トップページエラー: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # 2. 検索結果ページの調査（看護師 × 東京都で検索）
    print("2. 検索結果ページの調査")
    search_url = f"{base_url}/看護師の仕事-東京都?e=1"
    
    try:
        print(f"検索URL: {search_url}")
        response = session.get(search_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"✅ 検索結果ページ取得成功 (サイズ: {len(response.content)} bytes)")
            
            # ページタイトル
            title = soup.find('title')
            if title:
                print(f"ページタイトル: {title.get_text()}")
            
            # 主要なセクションを探す
            print("\n=== 主要なセクション調査 ===")
            main_sections = soup.find_all(['main', 'section', 'div'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['result', 'job', 'search', 'list']) if x else False)
            print(f"結果関連セクション: {len(main_sections)}個")
            
            for i, section in enumerate(main_sections[:3]):
                print(f"Section {i+1}: {section.name}, class='{section.get('class')}'")
                print(f"  内容プレビュー: {section.get_text(strip=True)[:100]}...")
            
            # 求人カード的な要素を探す
            print("\n=== 求人カード調査 ===")
            potential_job_cards = []
            
            # 様々なセレクタで求人カードを探す
            selectors_to_try = [
                'article',
                'section',
                'div[class*="job"]',
                'div[class*="card"]',
                'div[class*="result"]',
                'li[class*="job"]',
                '.job-card',
                '.jobCard',
                '[data-job]',
                '[data-jid]'
            ]
            
            for selector in selectors_to_try:
                elements = soup.select(selector)
                if elements:
                    print(f"セレクタ '{selector}': {len(elements)}個の要素発見")
                    potential_job_cards.extend(elements[:5])  # 最初の5個だけ
            
            # 重複を除去
            unique_cards = []
            seen_texts = set()
            for card in potential_job_cards:
                text = card.get_text(strip=True)[:50]
                if text not in seen_texts and len(text) > 10:
                    unique_cards.append(card)
                    seen_texts.add(text)
            
            print(f"\n重複除去後の求人カード候補: {len(unique_cards)}個")
            
            # 各求人カードの詳細を調査
            print("\n=== 求人カード詳細調査 ===")
            for i, card in enumerate(unique_cards[:5]):  # 最初の5個のみ
                print(f"\n--- カード {i+1} ---")
                print(f"要素: {card.name}")
                print(f"クラス: {card.get('class', [])}")
                print(f"ID: {card.get('id', 'なし')}")
                print(f"データ属性: {[attr for attr in card.attrs if attr.startswith('data-')]}")
                
                # カード内のリンクを調査
                links = card.find_all('a')
                print(f"カード内リンク数: {len(links)}")
                
                for j, link in enumerate(links[:3]):  # 最初の3個のリンクのみ
                    href = link.get('href', 'なし')
                    text = link.get_text(strip=True)[:30]
                    print(f"  Link {j+1}: href='{href}', text='{text}'")
                
                # カード内のテキスト内容（最初の100文字）
                card_text = card.get_text(strip=True)
                print(f"テキスト内容: {card_text[:100]}...")
        
        else:
            print(f"❌ 検索結果ページ取得失敗: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ 検索結果ページエラー: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # 3. 実際の詳細ページリンクを特定して調査
    print("3. 詳細ページリンクの特定")
    
    # 最も可能性の高い詳細ページリンクを探す
    all_links = soup.find_all('a')
    detail_link_candidates = []
    
    for link in all_links:
        href = link.get('href')
        if href:
            # 求人詳細ページらしいリンクを特定
            if any(pattern in href.lower() for pattern in ['/jb/', '/job/', 'detail']) and 'youtube' not in href.lower():
                if href.startswith('/'):
                    full_url = base_url + href
                elif href.startswith('http') and 'xn--pckua2a7gp15o89zb.com' in href:
                    full_url = href
                else:
                    continue
                
                # 重複を避ける
                if full_url not in [candidate['url'] for candidate in detail_link_candidates]:
                    detail_link_candidates.append({
                        'url': full_url,
                        'text': link.get_text(strip=True)[:50],
                        'original_href': href
                    })
    
    print(f"詳細ページリンク候補: {len(detail_link_candidates)}個")
    
    # 最初の3個の詳細ページを調査
    for i, candidate in enumerate(detail_link_candidates[:3]):
        print(f"\n=== 詳細ページ {i+1} 調査 ===")
        print(f"URL: {candidate['url']}")
        print(f"リンクテキスト: {candidate['text']}")
        
        try:
            time.sleep(2)  # レート制限
            detail_response = session.get(candidate['url'], headers=headers, timeout=30)
            
            if detail_response.status_code == 200:
                detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                print(f"✅ 詳細ページ取得成功 (サイズ: {len(detail_response.content)} bytes)")
                
                # ページタイトル
                detail_title = detail_soup.find('title')
                if detail_title:
                    print(f"ページタイトル: {detail_title.get_text()}")
                
                # 企業情報らしい要素を探す
                page_text = detail_soup.get_text()
                
                # 電話番号を探す
                import re
                phone_pattern = re.compile(r'(\d{2,4}[-‐]\d{2,4}[-‐]\d{4})')
                phone_matches = phone_pattern.findall(page_text)
                if phone_matches:
                    print(f"電話番号候補: {phone_matches[:3]}")
                
                # メールアドレスを探す
                email_pattern = re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')
                email_matches = email_pattern.findall(page_text)
                if email_matches:
                    valid_emails = [em for em in email_matches if 'youtube' not in em.lower() and '.png' not in em.lower()]
                    print(f"メールアドレス候補: {valid_emails[:3]}")
                
                # URLを探す（YouTubeを除外）
                url_pattern = re.compile(r'(https?://[^\s<>]+)')
                url_matches = url_pattern.findall(page_text)
                if url_matches:
                    valid_urls = [url for url in url_matches if 'youtube' not in url.lower() and 'xn--pckua2a7gp15o89zb.com' not in url]
                    print(f"外部URL候補: {valid_urls[:3]}")
                
                # 住所を探す
                address_pattern = re.compile(r'([東京都|大阪府|京都府|北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県].+?[市区町村].+?)(?:\n|$)', re.MULTILINE)
                address_matches = address_pattern.findall(page_text)
                if address_matches:
                    print(f"住所候補: {address_matches[0][:50]}...")
            
            else:
                print(f"❌ 詳細ページ取得失敗: {detail_response.status_code}")
        
        except Exception as e:
            print(f"❌ 詳細ページエラー: {e}")
    
    print("\n=== 調査完了 ===")

if __name__ == "__main__":
    debug_kyujinbox_structure() 