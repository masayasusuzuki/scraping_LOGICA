import streamlit as st
import pandas as pd
from scrapers.torabayu_scraper import TorabayuUI
from scrapers.biyou_nurse import BiyouNurseUI

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

# パスワード認証機能
def check_password():
    """パスワード認証を確認"""
    def password_entered():
        """ユーザーがパスワードを入力したときに呼ばれる"""
        if st.session_state["password"] == "Logica0312":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # パスワードをセッションから削除（セキュリティ）
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # タイトルとサブタイトルを黒色で表示（縦軸中央配置）
        st.markdown("""
        <style>
        .auth-container {
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            padding-top: 15vh;
            text-align: center;
        }
        
        .simple-title {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #000000;
            text-align: center;
            margin-bottom: 0.5rem;
            letter-spacing: 3px;
        }
        
        .simple-subtitle {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 0.9rem;
            color: #000000;
            text-align: center;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 中央配置コンテナの開始
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        # タイトルとサブタイトル
        st.markdown('<div class="simple-title">LOGICA SCRAPING</div>', unsafe_allow_html=True)
        st.markdown('<div class="simple-subtitle">Authentication Required</div>', unsafe_allow_html=True)
        
        # 入力フィールド
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.text_input(
                "Access Code", 
                on_change=password_entered, 
                key="password",
                placeholder="Enter authentication code"
            )
        
        # 中央配置コンテナの終了
        st.markdown('</div>', unsafe_allow_html=True)
        
        return False
    elif not st.session_state["password_correct"]:
        # エラー時のタイトルとサブタイトルを黒色で表示（縦軸中央配置）
        st.markdown("""
        <style>
        .auth-error-container {
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            padding-top: 15vh;
            text-align: center;
        }
        
        .simple-error-title {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #000000;
            text-align: center;
            margin-bottom: 0.5rem;
            letter-spacing: 3px;
        }
        
        .simple-error-message {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 0.9rem;
            color: #000000;
            text-align: center;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # エラー時の中央配置コンテナの開始
        st.markdown('<div class="auth-error-container">', unsafe_allow_html=True)
        
        # タイトルとエラーメッセージ
        st.markdown('<div class="simple-error-title">LOGICA SCRAPING</div>', unsafe_allow_html=True)
        st.markdown('<div class="simple-error-message">Invalid Authentication Code</div>', unsafe_allow_html=True)
        
        # 入力フィールド
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.text_input(
                "Access Code", 
                on_change=password_entered, 
                key="password",
                placeholder="Retry authentication code"
            )
        
        # エラー時の中央配置コンテナの終了
        st.markdown('</div>', unsafe_allow_html=True)
        
        return False
    else:
        # パスワードが正しい場合
        return True

# パスワード認証をチェック
if not check_password():
    st.stop()

# ライトモード固定とテーマ切り替えメニューを非表示にするCSS
st.markdown("""
<style>
/* ライトモードを強制する */
.stApp {
    color-scheme: light !important;
    background-color: white !important;
    color: black !important;
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

scraper_options = [
    "美容ナース.com",
    "とらばーゆ東京",
    "とらばーゆ神奈川", 
    "とらばーゆ千葉",
    "とらばーゆ埼玉"
]

selected_scraper = st.sidebar.radio(
    "サイトを選択してください",
    scraper_options,
    index=0
)

# メイン画面

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

# 検索結果の表示
if df_result is not None and not df_result.empty:
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
    <p>対応サイト: 美容ナース.com、とらばーゆ（東京・神奈川・千葉・埼玉）</p>
</div>
""", unsafe_allow_html=True) 