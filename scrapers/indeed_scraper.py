import streamlit as st
import pandas as pd
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse, parse_qs
import re

class IndeedUI:
    """Indeed専用のUIとスクレイピング機能"""
    
    # 設定定数
    BASE_URL = "https://jp.indeed.com/"
    
    # 日本の47都道府県リスト
    PREFECTURES = [
        "全国", "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
        "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
        "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
        "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
        "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
        "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
        "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
    ]
    
    def __init__(self):
        """初期化"""
        self.driver = None
    
    def render_ui(self):
        """Indeed専用のUIを表示"""
        st.header("Indeed：検索条件")
        
        # 検索条件入力部
        col1, col2 = st.columns(2)
        
        with col1:
            # キーワード入力
            keyword = st.text_input(
                "キーワード",
                placeholder="例：看護師、エンジニア、営業",
                key="indeed_keyword",
                help="職種、スキル、会社名などで検索できます"
            )
            
            # 都道府県選択
            prefecture = st.selectbox(
                "都道府県",
                self.PREFECTURES,
                index=0,
                key="indeed_prefecture"
            )
        
        with col2:
            # 取得ページ数
            max_pages = st.number_input(
                "取得ページ数",
                min_value=1,
                max_value=10,
                value=1,
                key="indeed_pages",
                help="各ページには約10件の求人が表示されます"
            )
            
            # ヘッドレスモード選択
            headless_mode = st.checkbox(
                "バックグラウンドで実行",
                value=True,
                key="indeed_headless",
                help="ブラウザを表示せずに実行します（推奨）"
            )
        
        # 詳細情報取得オプション
        get_details = st.checkbox(
            "詳細情報を取得する",
            value=True,
            key="indeed_get_details",
            help="各求人の詳細ページから追加情報を取得します（処理時間が長くなります）"
        )
        
        # 取得件数制限
        max_jobs = st.selectbox(
            "詳細取得する件数",
            [5, 10, 15, 20, 30, 50, 75, 100],
            index=1,  # デフォルトで10件
            key="indeed_max_jobs",
            help="詳細情報を取得する求人の最大件数"
        )
        
        # 実行部
        if st.button("この条件で検索する", type="primary", key="indeed_search"):
            # バリデーション
            if not keyword.strip():
                st.error("キーワードを入力してください。")
                return None
            
            search_params = {
                'keyword': keyword.strip(),
                'prefecture': prefecture if prefecture != "全国" else "",
                'max_pages': int(max_pages),
                'headless': headless_mode,
                'get_details': get_details,
                'max_jobs': max_jobs
            }
            
            with st.spinner("求人情報を取得中... しばらくお待ちください"):
                results = self.run_scraping(search_params)
                return results
        
        return None
    
    def setup_driver(self, headless=True):
        """WebDriverの設定"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless=new')  # 新しいヘッドレスモード
            
            # 安全性とパフォーマンスのオプション
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 最新のUser-Agentを使用
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
            
            # ログとブロック機能を制限
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # 画像読み込みを無効化
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # webdriver-managerを使用してChromeDriverを自動管理
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(15)  # 待機時間を延長
            return True
            
        except Exception as e:
            st.error(f"WebDriverの初期化に失敗しました: {str(e)}")
            st.error("Chromeブラウザがインストールされていることを確認してください。")
            return False
    
    def run_scraping(self, search_params):
        """Indeedから求人情報をスクレイピング"""
        try:
            # WebDriverの設定
            if not self.setup_driver(search_params['headless']):
                return {"error": "WebDriverの初期化に失敗しました"}
            
            all_jobs = []
            
            try:
                # Indeedトップページを開く
                st.info("Indeedにアクセス中...")
                self.driver.get(self.BASE_URL)
                
                # 検索フォームに入力
                self.perform_search(search_params['keyword'], search_params['prefecture'])
                
                # 指定ページ数まで求人を取得
                for page in range(1, search_params['max_pages'] + 1):
                    st.info(f"ページ {page}/{search_params['max_pages']} を処理中... (現在 {len(all_jobs)} 件取得済み)")
                    
                    # 現在のページから求人データを取得
                    jobs = self.extract_jobs_from_current_page()
                    
                    if not jobs:
                        st.warning(f"ページ {page} で求人が見つかりませんでした。")
                        break
                    
                    all_jobs.extend(jobs)
                    st.success(f"ページ {page} から {len(jobs)} 件の求人を取得しました。")
                    
                    # 次のページに移動（最後のページでない場合）
                    if page < search_params['max_pages']:
                        if not self.go_to_next_page():
                            st.info("次のページが見つかりません。検索結果の最後に到達しました。")
                            break
                        
                        # ページ間の待機時間
                        time.sleep(2)
                
                # 詳細情報取得
                if search_params.get('get_details', False) and all_jobs:
                    st.info("詳細情報を取得中...")
                    max_jobs = min(search_params.get('max_jobs', 10), len(all_jobs))
                    all_jobs = self.enrich_with_details_progressive(all_jobs[:max_jobs])
                    
                    # 詳細情報取得時は結果表示を抑制するためのフラグ付きで返す
                    if all_jobs:
                        df = pd.DataFrame(all_jobs)
                        df['情報源サイト名'] = 'Indeed'
                        return {"data": df, "progressive_display": True}
                    else:
                        st.warning("条件に合致する求人が見つかりませんでした。")
                        return {"data": pd.DataFrame(), "progressive_display": True}
                
                # 詳細情報取得なしの場合は通常のDataFrameを返す
                if all_jobs:
                    df = pd.DataFrame(all_jobs)
                    df['情報源サイト名'] = 'Indeed'
                    st.success(f"合計 {len(all_jobs)} 件の求人を取得しました。")
                    return df
                else:
                    st.warning("条件に合致する求人が見つかりませんでした。")
                    return pd.DataFrame()
                
            finally:
                # WebDriverのクリーンアップ
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                
        except Exception as e:
            st.error(f"スクレイピング中にエラーが発生しました: {str(e)}")
            
            # エラー時のクリーンアップ
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            return {"error": str(e)}
    
    def perform_search(self, keyword, prefecture):
        """検索フォームに入力して検索を実行"""
        try:
            # ページが完全に読み込まれるまで待機
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # 追加の待機時間
            
            # 複数のセレクタを試行してキーワード入力フィールドを探す
            keyword_input = None
            keyword_selectors = [
                "#text-input-what",
                "input[name='q']",
                "input[data-testid='jobs-search-box-keyword-input']",
                "input[placeholder*='職種、キーワード']",
                "input[aria-label*='職種']"
            ]
            
            for selector in keyword_selectors:
                try:
                    keyword_input = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not keyword_input:
                raise Exception("キーワード入力フィールドが見つかりませんでした")
            
            keyword_input.clear()
            keyword_input.send_keys(keyword)
            time.sleep(1)
            
            # 勤務地入力フィールドを探す
            location_input = None
            location_selectors = [
                "#text-input-where",
                "input[name='l']",
                "input[data-testid='jobs-search-box-location-input']",
                "input[placeholder*='都道府県']",
                "input[aria-label*='勤務地']"
            ]
            
            for selector in location_selectors:
                try:
                    location_input = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if location_input and prefecture:
                location_input.clear()
                location_input.send_keys(prefecture)
                time.sleep(1)
            
            # 検索ボタンを探してクリック
            search_button = None
            search_selectors = [
                "button[type='submit']",
                "button[data-testid='jobs-search-box-button']",
                ".yosegi-InlineWhatWhere-primaryButton",
                "input[type='submit']",
                "button:contains('求人検索')"
            ]
            
            for selector in search_selectors:
                try:
                    search_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not search_button:
                # Enterキーで検索を実行
                keyword_input.send_keys("\n")
            else:
                search_button.click()
            
            # 検索結果ページの読み込みを待機
            WebDriverWait(self.driver, 20).until(
                lambda driver: "求人検索" in driver.title or "jobs" in driver.current_url
            )
            
            time.sleep(3)  # 検索結果の安定化待機
            st.success("検索が完了しました。")
            
        except TimeoutException:
            st.error("検索フォームが見つからないか、検索結果の読み込みがタイムアウトしました。")
            raise
        except Exception as e:
            st.error(f"検索実行中にエラーが発生しました: {str(e)}")
            raise
    
    def extract_jobs_from_current_page(self):
        """現在のページから求人データを抽出"""
        try:
            jobs = []
            
            # ページが完全に読み込まれるまで待機
            time.sleep(3)
            
            # 複数の方法でJSONデータを取得を試行
            json_data = None
            json_scripts = [
                """
                try {
                    return window.mosaic.providerData["mosaic-provider-jobcards"].metaData.mosaicProviderJobCardsModel.results;
                } catch(e) {
                    return null;
                }
                """,
                """
                try {
                    return window._initialData?.results;
                } catch(e) {
                    return null;
                }
                """,
                """
                try {
                    const scripts = document.querySelectorAll('script');
                    for (let script of scripts) {
                        if (script.textContent.includes('window.mosaic') || script.textContent.includes('jobsearch')) {
                            const content = script.textContent;
                            if (content.includes('results')) {
                                return content;
                            }
                        }
                    }
                    return null;
                } catch(e) {
                    return null;
                }
                """
            ]
            
            for script in json_scripts:
                try:
                    json_data = self.driver.execute_script(script)
                    if json_data:
                        if isinstance(json_data, list):
                            # JSONデータから求人情報を抽出
                            for job_data in json_data:
                                job_info = self.parse_job_from_json(job_data)
                                if job_info:
                                    jobs.append(job_info)
                            break
                        elif isinstance(json_data, str) and "results" in json_data:
                            st.info("スクリプトデータを検出しました。HTMLパースに移行します。")
                            break
                except Exception:
                    continue
            
            # JSONからデータが取得できた場合はそれを返す
            if jobs:
                return jobs
            
            # フォールバック：HTMLから直接パース（改良版）
            st.info("HTMLから直接データを抽出します...")
            
            # 複数のセレクタパターンを試行
            job_selectors = [
                "[data-jk]",  # 従来のセレクタ
                ".job_seen_beacon",  # 新しいセレクタパターン
                ".slider_container .slider_item",
                ".jobsearch-SerpJobCard",
                "[data-tn-component='organicJob']",
                "a[data-jk]"
            ]
            
            job_elements = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_elements = elements
                        st.info(f"セレクタ '{selector}' で {len(elements)} 件の求人要素を発見")
                        break
                except Exception:
                    continue
            
            if not job_elements:
                st.warning("求人要素が見つかりませんでした。ページ構造を確認します。")
                # ページ構造のデバッグ情報を取得
                page_info = self.driver.execute_script("""
                    return {
                        title: document.title,
                        url: window.location.href,
                        hasResults: document.querySelector('[data-jk]') !== null,
                        hasJobCards: document.querySelector('.jobsearch-SerpJobCard') !== null,
                        elementCount: document.querySelectorAll('a').length
                    };
                """)
                st.warning(f"ページ情報: {page_info}")
                return []
            
            # 発見された要素から求人情報を抽出
            for i, job_element in enumerate(job_elements[:15]):  # 最大15件まで
                try:
                    job_info = self.parse_job_from_html_improved(job_element)
                    if job_info and any(job_info.values()):  # 空でない値があるかチェック
                        jobs.append(job_info)
                        if len(jobs) >= 10:  # 10件取得したら終了
                            break
                except Exception as e:
                    st.warning(f"求人 {i+1} のデータ解析中にエラー: {str(e)}")
                    continue
            
            return jobs
            
        except Exception as e:
            st.error(f"求人データの抽出中にエラーが発生しました: {str(e)}")
            return []
    
    def parse_job_from_json(self, job_data):
        """JSONデータから求人情報を解析"""
        try:
            job_info = {}
            
            # 基本情報
            job_info['職種名'] = job_data.get('title', '')
            job_info['会社名'] = job_data.get('company', '')
            job_info['勤務地'] = job_data.get('formattedLocation', '')
            job_info['給与'] = job_data.get('formattedSalary', '')
            job_info['雇用形態'] = job_data.get('formattedJobType', '')
            
            # 求人概要
            snippet = job_data.get('snippet', '')
            job_info['求人概要'] = snippet if snippet else ''
            
            # 詳細ページURL
            job_key = job_data.get('jobkey', '')
            if job_key:
                job_info['詳細ページURL'] = f"https://jp.indeed.com/viewjob?jk={job_key}"
            else:
                job_info['詳細ページURL'] = ''
            
            job_info['求人キー'] = job_key
            
            return job_info
            
        except Exception as e:
            st.warning(f"JSON求人データの解析エラー: {str(e)}")
            return None
    
    def parse_job_from_html(self, job_element):
        """HTML要素から求人情報を解析（従来版）"""
        try:
            job_info = {}
            
            # データ属性から求人キーを取得
            job_key = job_element.get_attribute('data-jk')
            job_info['求人キー'] = job_key if job_key else ''
            
            # 職種名
            try:
                title_element = job_element.find_element(By.CSS_SELECTOR, "h2 a span")
                job_info['職種名'] = title_element.get_attribute('title') or title_element.text
            except:
                job_info['職種名'] = ''
            
            # 会社名
            try:
                company_element = job_element.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']")
                job_info['会社名'] = company_element.text
            except:
                job_info['会社名'] = ''
            
            # 勤務地
            try:
                location_element = job_element.find_element(By.CSS_SELECTOR, "div[data-testid='job-location']")
                job_info['勤務地'] = location_element.text
            except:
                job_info['勤務地'] = ''
            
            # 給与
            try:
                salary_element = job_element.find_element(By.CSS_SELECTOR, "span[data-testid='job-salary']")
                job_info['給与'] = salary_element.text
            except:
                job_info['給与'] = ''
            
            # 雇用形態
            try:
                job_type_element = job_element.find_element(By.CSS_SELECTOR, "span[data-testid='job-type']")
                job_info['雇用形態'] = job_type_element.text
            except:
                job_info['雇用形態'] = ''
            
            # 求人概要
            try:
                snippet_element = job_element.find_element(By.CSS_SELECTOR, "div[data-testid='job-snippet']")
                job_info['求人概要'] = snippet_element.text
            except:
                job_info['求人概要'] = ''
            
            # 詳細ページURL
            if job_key:
                job_info['詳細ページURL'] = f"https://jp.indeed.com/viewjob?jk={job_key}"
            else:
                job_info['詳細ページURL'] = ''
            
            return job_info
            
        except Exception as e:
            st.warning(f"HTML求人データの解析エラー: {str(e)}")
            return None
    
    def parse_job_from_html_improved(self, job_element):
        """HTML要素から求人情報を解析（改良版）"""
        try:
            job_info = {}
            
            # データ属性から求人キーを取得（複数の方法を試行）
            job_key = ''
            try:
                job_key = job_element.get_attribute('data-jk') or ''
                if not job_key:
                    # リンク要素から求人キーを抽出
                    link_element = job_element.find_element(By.CSS_SELECTOR, "a[href*='jk=']")
                    href = link_element.get_attribute('href')
                    if href and 'jk=' in href:
                        job_key = href.split('jk=')[1].split('&')[0]
            except:
                pass
            
            job_info['求人キー'] = job_key
            
            # 職種名（複数のセレクタを試行）
            title_selectors = [
                "h2 a span[title]",
                "h2 a span",
                "h2 span",
                "a span[title]",
                ".jobTitle a span",
                "[data-testid='job-title'] a span",
                "h2.jobTitle a span"
            ]
            
            title = ''
            for selector in title_selectors:
                try:
                    title_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.get_attribute('title') or title_element.text
                    if title:
                        break
                except:
                    continue
            
            job_info['職種名'] = title.strip()
            
            # 会社名（複数のセレクタを試行）
            company_selectors = [
                "span[data-testid='company-name']",
                ".companyName",
                "[data-testid='company-name']",
                "a[data-testid='company-name']",
                "span.companyName"
            ]
            
            company = ''
            for selector in company_selectors:
                try:
                    company_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    company = company_element.text
                    if company:
                        break
                except:
                    continue
            
            job_info['会社名'] = company.strip()
            
            # 勤務地（複数のセレクタを試行）
            location_selectors = [
                "div[data-testid='job-location']",
                ".companyLocation",
                "[data-testid='job-location']",
                "div.companyLocation"
            ]
            
            location = ''
            for selector in location_selectors:
                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    location = location_element.text
                    if location:
                        break
                except:
                    continue
            
            job_info['勤務地'] = location.strip()
            
            # 給与（複数のセレクタを試行）
            salary_selectors = [
                "span[data-testid='job-salary']",
                ".salaryText",
                "[data-testid='job-salary']",
                ".salary-snippet"
            ]
            
            salary = ''
            for selector in salary_selectors:
                try:
                    salary_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    salary = salary_element.text
                    if salary:
                        break
                except:
                    continue
            
            job_info['給与'] = salary.strip()
            
            # 雇用形態（複数のセレクタを試行）
            job_type_selectors = [
                "span[data-testid='job-type']",
                ".jobType",
                "[data-testid='job-type']"
            ]
            
            job_type = ''
            for selector in job_type_selectors:
                try:
                    job_type_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    job_type = job_type_element.text
                    if job_type:
                        break
                except:
                    continue
            
            job_info['雇用形態'] = job_type.strip()
            
            # 求人概要（複数のセレクタを試行）
            snippet_selectors = [
                "div[data-testid='job-snippet']",
                ".summary",
                "[data-testid='job-snippet']",
                ".job-snippet"
            ]
            
            snippet = ''
            for selector in snippet_selectors:
                try:
                    snippet_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    snippet = snippet_element.text
                    if snippet:
                        break
                except:
                    continue
            
            job_info['求人概要'] = snippet.strip()
            
            # 詳細ページURL
            if job_key:
                job_info['詳細ページURL'] = f"https://jp.indeed.com/viewjob?jk={job_key}"
            else:
                # リンクから直接URLを取得
                try:
                    link_element = job_element.find_element(By.CSS_SELECTOR, "a[href*='viewjob']")
                    href = link_element.get_attribute('href')
                    if href:
                        job_info['詳細ページURL'] = href
                    else:
                        job_info['詳細ページURL'] = ''
                except:
                    job_info['詳細ページURL'] = ''
            
            return job_info
            
        except Exception as e:
            st.warning(f"改良版HTML求人データの解析エラー: {str(e)}")
            return None
    
    def enrich_with_details(self, jobs):
        """求人リストに詳細情報を追加"""
        enriched_jobs = []
        
        for i, job in enumerate(jobs):
            try:
                st.info(f"詳細情報取得中... ({i+1}/{len(jobs)})")
                
                detail_url = job.get('詳細ページURL', '')
                if not detail_url:
                    enriched_jobs.append(job)
                    continue
                
                # 詳細情報を取得
                detail_info = self.get_job_details(detail_url)
                
                # 基本情報と詳細情報をマージ
                enriched_job = {**job, **detail_info}
                enriched_jobs.append(enriched_job)
                
                # サーバーへの配慮
                time.sleep(2)
                
            except Exception as e:
                st.warning(f"求人 {i+1} の詳細情報取得中にエラー: {str(e)}")
                enriched_jobs.append(job)  # エラー時は基本情報のみ保持
                continue
        
        return enriched_jobs
    
    def enrich_with_details_progressive(self, jobs):
        """求人リストに詳細情報を追加（1件ずつ表示）"""
        enriched_jobs = []
        
        # 結果表示用のプレースホルダーを作成
        results_placeholder = st.empty()
        status_placeholder = st.empty()
        
        for i, job in enumerate(jobs):
            try:
                status_placeholder.info(f"詳細情報取得中... ({i+1}/{len(jobs)}) - {job.get('職種名', '求人')}")
                
                detail_url = job.get('詳細ページURL', '')
                if not detail_url:
                    enriched_jobs.append(job)
                    
                    # 詳細情報なしでもテーブルを更新
                    if enriched_jobs:
                        df_temp = pd.DataFrame(enriched_jobs)
                        df_temp['情報源サイト名'] = 'Indeed'
                        
                        # Indeed用の詳細表示カラム
                        indeed_columns = [
                            '職種名', '会社名', '勤務地', '給与', '雇用形態', '詳細ページURL',
                            '職務内容', '必要スキル', '福利厚生', '勤務時間', '企業情報', '応募方法'
                        ]
                        available_indeed_columns = [col for col in indeed_columns if col in df_temp.columns]
                        
                        if available_indeed_columns:
                            results_placeholder.dataframe(
                                df_temp[available_indeed_columns],
                                use_container_width=True,
                                hide_index=True,
                                height=min(400 + len(enriched_jobs) * 35, 800)
                            )
                        else:
                            results_placeholder.dataframe(
                                df_temp,
                                use_container_width=True,
                                hide_index=True,
                                height=min(400 + len(enriched_jobs) * 35, 800)
                            )
                    continue
                
                # 詳細情報を取得
                detail_info = self.get_job_details(detail_url)
                
                # 基本情報と詳細情報をマージ
                enriched_job = {**job, **detail_info}
                enriched_jobs.append(enriched_job)
                
                # 1件処理完了後、即座にテーブルを更新表示
                if enriched_jobs:
                    df_temp = pd.DataFrame(enriched_jobs)
                    df_temp['情報源サイト名'] = 'Indeed'
                    
                    # Indeed用の詳細表示カラム
                    indeed_columns = [
                        '職種名', '会社名', '勤務地', '給与', '雇用形態', '詳細ページURL',
                        '職務内容', '必要スキル', '福利厚生', '勤務時間', '企業情報', '応募方法'
                    ]
                    available_indeed_columns = [col for col in indeed_columns if col in df_temp.columns]
                    
                    if available_indeed_columns:
                        results_placeholder.dataframe(
                            df_temp[available_indeed_columns],
                            use_container_width=True,
                            hide_index=True,
                            height=min(400 + len(enriched_jobs) * 35, 800)
                        )
                    else:
                        results_placeholder.dataframe(
                            df_temp,
                            use_container_width=True,
                            hide_index=True,
                            height=min(400 + len(enriched_jobs) * 35, 800)
                        )
                
                # サーバーへの配慮
                time.sleep(2)
                
            except Exception as e:
                st.warning(f"求人 {i+1} の詳細情報取得中にエラー: {str(e)}")
                enriched_jobs.append(job)  # エラー時は基本情報のみ保持
                
                # エラー時でもテーブルを更新
                if enriched_jobs:
                    df_temp = pd.DataFrame(enriched_jobs)
                    df_temp['情報源サイト名'] = 'Indeed'
                    
                    # Indeed用の詳細表示カラム
                    indeed_columns = [
                        '職種名', '会社名', '勤務地', '給与', '雇用形態', '詳細ページURL',
                        '職務内容', '必要スキル', '福利厚生', '勤務時間', '企業情報', '応募方法'
                    ]
                    available_indeed_columns = [col for col in indeed_columns if col in df_temp.columns]
                    
                    if available_indeed_columns:
                        results_placeholder.dataframe(
                            df_temp[available_indeed_columns],
                            use_container_width=True,
                            hide_index=True,
                            height=min(400 + len(enriched_jobs) * 35, 800)
                        )
                    else:
                        results_placeholder.dataframe(
                            df_temp,
                            use_container_width=True,
                            hide_index=True,
                            height=min(400 + len(enriched_jobs) * 35, 800)
                        )
                continue
        
        # 処理完了後のステータス更新
        status_placeholder.success(f"詳細情報取得完了！ {len(enriched_jobs)}件の求人情報を取得しました。")
        
        return enriched_jobs
    
    def get_job_details(self, detail_url):
        """詳細ページから追加情報を取得"""
        try:
            # 詳細ページに移動
            self.driver.get(detail_url)
            
            # ページの読み込みを待機
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            
            detail_info = {}
            
            # 職務内容
            job_description_selectors = [
                "#jobDescriptionText",
                ".jobsearch-jobDescriptionText",
                "[data-testid='job-description']",
                ".jobDescriptionContent"
            ]
            
            description = ''
            for selector in job_description_selectors:
                try:
                    desc_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    description = desc_element.text
                    if description:
                        break
                except:
                    continue
            
            detail_info['職務内容'] = description.strip()[:500] if description else ''  # 500文字制限
            
            # 必要なスキル・経験
            skills_selectors = [
                "div:contains('必要なスキル')",
                "div:contains('求めるスキル')",
                "div:contains('応募要件')",
                "div:contains('必須条件')"
            ]
            
            skills = ''
            try:
                skills_text = self.driver.execute_script("""
                    const elements = Array.from(document.querySelectorAll('*'));
                    const skillsElements = elements.filter(el => 
                        el.textContent.includes('必要なスキル') || 
                        el.textContent.includes('求めるスキル') ||
                        el.textContent.includes('応募要件') ||
                        el.textContent.includes('必須条件')
                    );
                    if (skillsElements.length > 0) {
                        return skillsElements[0].textContent;
                    }
                    return '';
                """)
                skills = skills_text[:300] if skills_text else ''
            except:
                pass
            
            detail_info['必要スキル'] = skills.strip()
            
            # 福利厚生
            benefits_text = ''
            try:
                benefits_script = self.driver.execute_script("""
                    const elements = Array.from(document.querySelectorAll('*'));
                    const benefitsElements = elements.filter(el => 
                        el.textContent.includes('福利厚生') || 
                        el.textContent.includes('待遇') ||
                        el.textContent.includes('手当') ||
                        el.textContent.includes('保険')
                    );
                    if (benefitsElements.length > 0) {
                        return benefitsElements[0].textContent;
                    }
                    return '';
                """)
                benefits_text = benefits_script[:300] if benefits_script else ''
            except:
                pass
            
            detail_info['福利厚生'] = benefits_text.strip()
            
            # 勤務時間
            working_hours = ''
            try:
                hours_script = self.driver.execute_script("""
                    const elements = Array.from(document.querySelectorAll('*'));
                    const hoursElements = elements.filter(el => 
                        el.textContent.includes('勤務時間') || 
                        el.textContent.includes('就業時間') ||
                        el.textContent.includes('営業時間')
                    );
                    if (hoursElements.length > 0) {
                        return hoursElements[0].textContent;
                    }
                    return '';
                """)
                working_hours = hours_script[:200] if hours_script else ''
            except:
                pass
            
            detail_info['勤務時間'] = working_hours.strip()
            
            # 企業情報
            company_info = ''
            try:
                company_selectors = [
                    "[data-testid='company-overview']",
                    ".icl-u-lg-mr--sm",
                    ".jobsearch-CompanyReview"
                ]
                
                for selector in company_selectors:
                    try:
                        company_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        company_info = company_element.text
                        if company_info:
                            break
                    except:
                        continue
                        
                company_info = company_info[:300] if company_info else ''
            except:
                pass
            
            detail_info['企業情報'] = company_info.strip()
            
            # 応募方法
            application_info = ''
            try:
                app_script = self.driver.execute_script("""
                    const elements = Array.from(document.querySelectorAll('*'));
                    const appElements = elements.filter(el => 
                        el.textContent.includes('応募方法') || 
                        el.textContent.includes('選考プロセス') ||
                        el.textContent.includes('面接')
                    );
                    if (appElements.length > 0) {
                        return appElements[0].textContent;
                    }
                    return '';
                """)
                application_info = app_script[:200] if app_script else ''
            except:
                pass
            
            detail_info['応募方法'] = application_info.strip()
            
            return detail_info
            
        except Exception as e:
            st.warning(f"詳細ページの解析中にエラー: {str(e)}")
            return {}
    
    def go_to_next_page(self):
        """次のページに移動"""
        try:
            # 次のページボタンを探してクリック
            next_button = self.driver.find_element(By.CSS_SELECTOR, "a[aria-label='Next Page']")
            
            if next_button and next_button.is_enabled():
                next_button.click()
                
                # 新しいページの読み込みを待機
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-jk]"))
                )
                
                return True
            else:
                return False
                
        except (NoSuchElementException, TimeoutException):
            # 次のページボタンが見つからない場合は最後のページ
            return False
        except Exception as e:
            st.warning(f"次のページへの移動中にエラー: {str(e)}")
            return False 