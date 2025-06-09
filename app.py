import streamlit as st
import pandas as pd
from scrapers.torabayu_scraper import TorabayuUI
from scrapers.biyou_nurse import BiyouNurseUI
from scrapers.kyujinbox_scraper import KyujinboxUI

# ページ設定
st.set_page_config(
    page_title="LOGICA SCRAPING",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)



# ライトモード・ダークモード両対応のCSS
st.markdown("""
<style>
/* CSS変数を定義 */
:root {
    --text-color: #000000;
    --bg-color: #ffffff;
}

/* ダークモードのCSS変数 */
[data-theme="dark"] {
    --text-color: #ffffff;
    --bg-color: #0e1117;
}

/* より確実なダークモード検出 */
.stApp[data-baseweb-theme="dark"] {
    --text-color: #ffffff !important;
    --bg-color: #0e1117 !important;
    background-color: #0e1117 !important;
    color: #ffffff !important;
}

/* 全体のテキスト色を統一 */
.stApp,
.main,
.main .block-container,
div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"],
.stMarkdown,
.stMarkdown p,
.stMarkdown h1,
.stMarkdown h2, 
.stMarkdown h3,
.stMarkdown h4,
.stMarkdown h5,
.stMarkdown h6,
.stText {
    color: var(--text-color, #000000) !important;
}

/* ダークモード時の全体背景 */
.stApp[data-baseweb-theme="dark"],
.stApp[data-baseweb-theme="dark"] .main,
.stApp[data-baseweb-theme="dark"] .main .block-container {
    background-color: #0e1117 !important;
    color: #ffffff !important;
}

/* ダークモード時の全てのテキスト要素 */
.stApp[data-baseweb-theme="dark"] .stMarkdown,
.stApp[data-baseweb-theme="dark"] .stMarkdown p,
.stApp[data-baseweb-theme="dark"] .stMarkdown h1,
.stApp[data-baseweb-theme="dark"] .stMarkdown h2,
.stApp[data-baseweb-theme="dark"] .stMarkdown h3,
.stApp[data-baseweb-theme="dark"] .stMarkdown h4,
.stApp[data-baseweb-theme="dark"] .stMarkdown h5,
.stApp[data-baseweb-theme="dark"] .stMarkdown h6,
.stApp[data-baseweb-theme="dark"] .stText,
.stApp[data-baseweb-theme="dark"] div[data-testid="stVerticalBlock"],
.stApp[data-baseweb-theme="dark"] div[data-testid="stHorizontalBlock"] {
    color: #ffffff !important;
}

/* ダークモード時の入力フィールド */
.stApp[data-baseweb-theme="dark"] .stTextInput > div > div > input {
    background-color: #262730 !important;
    color: #ffffff !important;
    border-color: #555555 !important;
}

/* ダークモード時のセレクトボックス */
.stApp[data-baseweb-theme="dark"] .stSelectbox > div > div {
    background-color: #262730 !important;
    color: #ffffff !important;
}

/* ダークモード時のボタン */
.stApp[data-baseweb-theme="dark"] .stButton > button {
    background-color: #262730 !important;
    color: #ffffff !important;
    border: 1px solid #555555 !important;
}

.stApp[data-baseweb-theme="dark"] .stButton > button:hover {
    background-color: #3c3c43 !important;
    color: #ffffff !important;
}

/* ダークモード時のデータフレーム */
.stApp[data-baseweb-theme="dark"] .stDataFrame,
.stApp[data-baseweb-theme="dark"] .stDataFrame table,
.stApp[data-baseweb-theme="dark"] .stDataFrame th,
.stApp[data-baseweb-theme="dark"] .stDataFrame td {
    background-color: #262730 !important;
    color: #ffffff !important;
}

/* ダークモード時のメトリクス */
.stApp[data-baseweb-theme="dark"] div[data-testid="metric-container"],
.stApp[data-baseweb-theme="dark"] div[data-testid="metric-container"] * {
    color: #ffffff !important;
}

/* 共通スタイル（両モード共通） */
.stButton > button[kind="primary"] {
    background-color: #0066cc !important;
    color: white !important;
    border: none !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #0052a3 !important;
    color: white !important;
}

/* 成功・警告・エラーメッセージ（両モード対応） */
.stSuccess {
    background-color: #d4edda !important;
    color: #155724 !important;
}

.stWarning {
    background-color: #fff3cd !important;
    color: #856404 !important;
}

.stError {
    background-color: #f8d7da !important;
    color: #721c24 !important;
}

.stInfo {
    background-color: #d1ecf1 !important;
    color: #0c5460 !important;
}

/* メインメニューボタンを非表示 */
button[kind="header"] {
    display: none !important;
}

/* テーマ切り替えボタンを非表示 */
button[data-testid="stDecoration"] {
    display: none !important;
}

/* ヘッダーの設定メニューを非表示 */
section[data-testid="stHeader"] button[aria-label="View app menu, other links, and options"] {
    display: none !important;
}

/* Streamlitのデフォルトメニューを非表示 */
#MainMenu {
    visibility: hidden !important;
}

/* ヘッダーを非表示（完全にクリーンな見た目にする場合） */
header[data-testid="stHeader"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# カスタムCSS - サイドバーデザイン
st.markdown("""
<style>
/* サイドバーの背景色を高級感ある黒に */
section[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
    border-right: 3px solid #444444 !important;
}

section[data-testid="stSidebar"] > div {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
    padding-top: 2rem !important;
}

/* サイドバー内のテキスト色を白に */
section[data-testid="stSidebar"] * {
    color: white !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
    font-weight: 700 !important;
    margin-bottom: 1.5rem !important;
    padding-bottom: 0.8rem !important;
    border-bottom: 2px solid #555555 !important;
    text-align: center !important;
    letter-spacing: 2px !important;
    font-family: 'Arial', sans-serif !important;
}

/* ラジオボタンのスタイリング */
section[data-testid="stSidebar"] label {
    color: #e5e7eb !important;
    font-weight: 500 !important;
    font-size: 14px !important;
}

/* ラジオボタンのオプション項目のホバー効果のみ適用 */
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
    color: #ffffff !important;
    background-color: rgba(255, 255, 255, 0.1) !important;
    border-radius: 5px !important;
    padding: 4px 8px !important;
    transition: all 0.3s ease !important;
}

/* ラジオボタンのタイトル部分（「サイトを選択してください」）のホバー効果を無効化 */
section[data-testid="stSidebar"] div[data-testid="stRadio"] > label:first-child {
    color: #ffffff !important;
    font-weight: 600 !important;
    pointer-events: none !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] > label:first-child:hover {
    background-color: transparent !important;
    padding: 0 !important;
}

/* ラジオボタンの選択状態 */
section[data-testid="stSidebar"] input[type="radio"]:checked + label {
    color: #ffffff !important;
    font-weight: 600 !important;
    background-color: rgba(255, 255, 255, 0.2) !important;
    border-radius: 5px !important;
    padding: 6px 10px !important;
}

/* チェックボックスのスタイリング */
section[data-testid="stSidebar"] .stCheckbox {
    margin-top: 1rem !important;
}

section[data-testid="stSidebar"] .stCheckbox label {
    font-size: 13px !important;
    color: #cccccc !important;
}

/* レガシー対応 */
.css-1d391kg,
.css-1outpf7,
.st-emotion-cache-16txtl3 {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
}

.css-1d391kg *,
.css-1outpf7 *,
.st-emotion-cache-16txtl3 * {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# サイドバーでスクレイパーを選択
st.sidebar.title("LOGICA SCRAPING")

# メインメニューの選択
main_menu = st.sidebar.radio(
    "メニューを選択してください",
    ["スクレイピング", "機能改善"],
    index=0
)

if main_menu == "スクレイピング":
    scraper_options = [
        "美容ナース.com",
        "とらばーゆ東京",
        "とらばーゆ神奈川", 
        "とらばーゆ千葉",
        "とらばーゆ埼玉",
        "求人ボックス"
    ]

    selected_scraper = st.sidebar.radio(
        "サイトを選択してください",
        scraper_options,
        index=0
    )

# メイン画面

if main_menu == "スクレイピング":
    # 選択されたスクレイパーに基づいてUIを表示
    df_result = None

    if selected_scraper == "美容ナース.com":
        # 美容ナースUIを表示
        biyou_nurse_ui = BiyouNurseUI()
        df_result = biyou_nurse_ui.render_ui()

    elif selected_scraper == "とらばーゆ東京":
        # とらばーゆ東京UIを表示
        torabayu_ui = TorabayuUI(region="tokyo")
        df_result = torabayu_ui.render_ui()

    elif selected_scraper == "とらばーゆ神奈川":
        # とらばーゆ神奈川UIを表示
        torabayu_ui = TorabayuUI(region="kanagawa")
        df_result = torabayu_ui.render_ui()

    elif selected_scraper == "とらばーゆ千葉":
        # とらばーゆ千葉UIを表示
        torabayu_ui = TorabayuUI(region="chiba")
        df_result = torabayu_ui.render_ui()

    elif selected_scraper == "とらばーゆ埼玉":
        # とらばーゆ埼玉UIを表示
        torabayu_ui = TorabayuUI(region="saitama")
        df_result = torabayu_ui.render_ui()

    elif selected_scraper == "求人ボックス":
        # 求人ボックスUIを表示
        kyujinbox_ui = KyujinboxUI()
        df_result = kyujinbox_ui.render_ui()

elif main_menu == "機能改善":
    import os
    import gspread
    from google.oauth2.service_account import Credentials
    import json
    from datetime import datetime
    
    def get_google_credentials():
        """Google認証情報を取得（環境変数優先、ファイル次点）"""
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # 方法1: Streamlit Secretsから取得
        try:
            if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
                return Credentials.from_service_account_info(st.secrets['gcp_service_account'], scopes=scope)
        except:
            pass
        
        # 方法2: 環境変数から取得
        if os.environ.get('GOOGLE_SERVICE_ACCOUNT'):
            try:
                service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
                return Credentials.from_service_account_info(service_account_info, scopes=scope)
            except:
                pass
        
        # 方法3: ファイルから取得
        if os.path.exists('service_account_key.json'):
            return Credentials.from_service_account_file('service_account_key.json', scopes=scope)
        
        raise FileNotFoundError("Google認証情報が見つかりません")
    
    # 機能改善要望フォーム
    st.header("機能改善要望")
    st.markdown("アプリの改善提案をお聞かせください。いただいたご意見は今後の開発に活用させていただきます。")
    
    with st.form("improvement_form", clear_on_submit=True):
        st.subheader("要望内容")
        
        # 名前の入力
        name = st.text_input(
            "お名前 *",
            placeholder="お名前をご入力ください",
            help="必須項目です"
        )
        
        # 改善要望の入力
        improvement_request = st.text_area(
            "機能改善要望 *",
            placeholder="改善したい機能や新しく追加したい機能について詳しくお聞かせください",
            height=150,
            help="具体的にご記入いただけると助かります"
        )
        
        # 入力日
        input_date = st.date_input(
            "入力日",
            help="要望を入力する日付を選択してください"
        )
        
        # 希望実装日
        desired_date = st.date_input(
            "希望実装日（参考）",
            help="実装を希望される時期の目安があれば選択してください"
        )
        
        # 送信ボタン
        submitted = st.form_submit_button("要望を送信", use_container_width=True)
        
        if submitted:
            # バリデーション
            if not name.strip():
                st.error("お名前を入力してください。")
            elif not improvement_request.strip():
                st.error("機能改善要望を入力してください。")
            else:
                # Google Sheetsに送信する処理
                try:
                    # Google認証情報を取得
                    try:
                        creds = get_google_credentials()
                        client = gspread.authorize(creds)
                        
                        # スプレッドシートを開く
                        sheet_id = "1jTjdTEB2eT_3hFnoav1reyZFFz8RmsQGoL8DZc-E9cU"
                        spreadsheet = client.open_by_key(sheet_id)
                        worksheet = spreadsheet.worksheet("ツール改善案")
                        
                        # データを追加（A列=名前、B列=要望、C列=入力日、D列=希望実装日）
                        row_data = [
                            name.strip(),
                            improvement_request.strip(),
                            input_date.strftime("%Y-%m-%d"),
                            desired_date.strftime("%Y-%m-%d")
                        ]
                        
                        worksheet.append_row(row_data)
                        
                        st.success("要望を送信しました。貴重なご意見をありがとうございます。")
                        
                    except FileNotFoundError:
                        st.error("Google Sheets APIの設定が完了していません。環境変数またはファイルで認証情報を設定してください。")
                        
                        # 設定手順を表示
                        with st.expander("Google Sheets API設定手順", expanded=True):
                            st.markdown("""
                            ### 1. Google Cloud Consoleでプロジェクトを作成・選択
                            
                            1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
                            2. 新しいプロジェクトを作成するか、既存のプロジェクトを選択
                            
                            ### 2. Google Sheets APIを有効化
                            
                            1. Google Cloud Consoleで「APIとサービス」→「ライブラリ」に移動
                            2. 「Google Sheets API」を検索して有効化
                            3. 「Google Drive API」も検索して有効化
                            
                            ### 3. サービスアカウントを作成
                            
                            1. 「APIとサービス」→「認証情報」に移動
                            2. 「認証情報を作成」→「サービスアカウント」を選択
                            3. サービスアカウント名を入力（例：logica-scraping-service）
                            4. 「作成して続行」をクリック
                            5. ロールは「編集者」を選択
                            6. 「完了」をクリック
                            
                            ### 4. サービスアカウントキーを作成・ダウンロード
                            
                            1. 作成したサービスアカウントをクリック
                            2. 「キー」タブに移動
                            3. 「キーを追加」→「新しいキーを作成」を選択
                            4. キーのタイプは「JSON」を選択
                            5. 「作成」をクリックしてJSONファイルをダウンロード
                            6. ダウンロードしたファイルを `service_account_key.json` という名前でこのアプリのフォルダに配置
                            
                            ### 5. スプレッドシートの共有設定
                            
                            1. [こちらのスプレッドシート](https://docs.google.com/spreadsheets/d/1jTjdTEB2eT_3hFnoav1reyZFFz8RmsQGoL8DZc-E9cU/edit?usp=sharing) を開く
                            2. 右上の「共有」ボタンをクリック
                            3. サービスアカウントのメールアドレス（service_account_key.jsonファイル内の`client_email`）を追加
                            4. 権限を「編集者」に設定
                            5. 「送信」をクリック
                            
                            ### 6. 設定完了の確認
                            
                            - `service_account_key.json` ファイルがアプリフォルダに配置されていること
                            - スプレッドシートがサービスアカウントと共有されていること
                            - スプレッドシート内に「ツール改善案」シートが存在すること
                            
                            設定完了後、再度要望を送信してください。
                            """)
                        
                except Exception as e:
                    st.error(f"送信中にエラーが発生しました: {str(e)}")
                    st.info("管理者にお問い合わせください。")
    
    # 送信済み要望の確認（管理者向け）
    st.divider()
    st.subheader("送信済み要望一覧")
    
    # ページ読み込み時に自動でデータを取得・表示
    try:
        creds = get_google_credentials()
        client = gspread.authorize(creds)
        
        sheet_id = "1jTjdTEB2eT_3hFnoav1reyZFFz8RmsQGoL8DZc-E9cU"
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet("ツール改善案")
        
        # 全データを確実に取得（明示的に範囲を指定）
        # まず使用範囲を確認
        try:
            # A1から最後のデータまでの範囲を取得
            all_values = worksheet.get_all_values()
            
            # 空行を除去せずに全データを取得（デバッグ用情報も含める）
            data = all_values
            

            
        except Exception as e:
            st.error(f"データ取得エラー: {str(e)}")
            # 代替手段として明示的に範囲を指定
            try:
                data = worksheet.get('A:D')  # A列からD列まで全て取得
            except Exception as e2:
                st.error(f"代替データ取得もエラー: {str(e2)}")
                data = []
        
        if data:
            if len(data) > 0:
                # 正しいヘッダーを定義
                expected_headers = ['名前', '要望', '入力日', '希望実装日']
                
                # 1行目がヘッダー行かデータ行かを判断
                first_row = data[0]
                is_header_row = (first_row == expected_headers)
                
                if is_header_row:
                    # 1行目がヘッダー行の場合
                    headers = first_row
                    data_rows = data[1:] if len(data) > 1 else []
                else:
                    # 1行目からデータ行の場合（ヘッダー行が存在しない）
                    headers = expected_headers
                    data_rows = data  # 1行目からすべてデータとして扱う
                
                if data_rows:
                    # DataFrameに変換
                    df = pd.DataFrame(data_rows, columns=headers)
                    
                    # シンプルな表として表示
                    st.dataframe(
                        df,
                        use_container_width=True,
                        column_config={
                            "名前": st.column_config.TextColumn("名前", width="small"),
                            "要望": st.column_config.TextColumn("要望", width="large"),
                            "入力日": st.column_config.TextColumn("入力日", width="small"),
                            "希望実装日": st.column_config.TextColumn("希望実装日", width="small"),
                        }
                    )
                    
                    # 統計情報を表示
                    st.success(f"{len(df)}件の要望が登録されています。")
                        
                else:
                    st.info("まだ要望が登録されていません。")
            else:
                st.info("まだ要望が登録されていません。")
        else:
            st.info("まだ要望が登録されていません。")
            
    except FileNotFoundError:
        st.warning("Google Sheets APIの設定が必要です。環境変数またはファイルで認証情報を設定してください。")
    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {str(e)}")
    
    # 手動更新ボタン
    if st.button("最新データを再読み込み", use_container_width=True):
        st.rerun()

# 検索結果の表示
if main_menu == "スクレイピング" and 'df_result' in locals() and df_result is not None and not df_result.empty:
    st.divider()
    st.subheader("📊 検索結果")
    
    # 統計情報
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("取得件数", len(df_result))
    with col2:
        # 電話番号カラムが存在するかチェック
        phone_col = '電話番号' if '電話番号' in df_result.columns else None
        if phone_col:
            phone_count = len(df_result[df_result[phone_col] != ''])
            st.metric("電話番号あり", phone_count)
        else:
            st.metric("電話番号あり", 0)
    with col3:
        # 代表者名カラムが存在するかチェック  
        rep_col = '代表者名' if '代表者名' in df_result.columns else None
        if rep_col:
            rep_count = len(df_result[df_result[rep_col] != ''])
            st.metric("代表者名あり", rep_count)
        else:
            st.metric("代表者名あり", 0)
    
    # データフレームを表示（統一されたヘッダー順序）
    # カラム順序を統一
    preferred_columns = ['施設名', '代表者名', '住所', 'WebサイトURL', '電話番号', 'メールアドレス', '事業内容']
    
    # 存在するカラムのみを選択し、順序を調整
    available_columns = []
    for col in preferred_columns:
        if col in df_result.columns:
            available_columns.append(col)
    
    # 残りのカラムも追加（後方に配置）
    for col in df_result.columns:
        if col not in available_columns:
            available_columns.append(col)
    
    # カラム順序に従ってデータフレームを再構成
    df_display = df_result[available_columns]
    
    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
        column_config={
            "施設名": st.column_config.TextColumn("施設名（会社名）", width="medium"),
            "代表者名": st.column_config.TextColumn("代表者名", width="small"),
            "住所": st.column_config.TextColumn("住所", width="large"),
            "WebサイトURL": st.column_config.LinkColumn("WebサイトURL", width="medium"),
            "電話番号": st.column_config.TextColumn("電話番号", width="small"),
            "メールアドレス": st.column_config.TextColumn("メールアドレス", width="medium"),
            "事業内容": st.column_config.TextColumn("事業内容", width="large"),
            # 後方互換性のため既存カラムも対応
            "勤務地": st.column_config.TextColumn("勤務地", width="large"),
            "求人URL": st.column_config.LinkColumn("求人URL", width="medium"),
            "業務内容": st.column_config.TextColumn("業務内容", width="large")
        }
    )
    
    # CSVダウンロード機能
    csv = df_result.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSVダウンロード",
        data=csv,
        file_name=f"{selected_scraper}_求人情報_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# フッター
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 14px;'>
    <p>LOGICA SCRAPING</p>
    <p>対応サイト: 美容ナース.com、とらばーゆ（東京・神奈川・千葉・埼玉）、求人ボックス</p>
</div>
""", unsafe_allow_html=True) 